#include "engine/asd_texture.h"
#include "engine/asd_symbols.h"
#include <cstdint>

// ---------------------------------------------------------------------------
// Observed call targets (addresses are the branch targets in code.bin)
// ---------------------------------------------------------------------------

extern "C" {
    // AsdMemory (c:\SMT4\XRD686\AsdSDK\Source\Sys\Mem\AsdMemory.cpp)
    void* AsdMem_Alloc(u32 a0, u32 a1, u32 a2, u32 size, u32 flag);         // 0x002c4b84
    void* AsdMem_AllocAlign(u32 a0, u32 a1, u32 a2, u32 size, u32 flag);    // 0x002c54f0
    void  AsdMem_Zero(void* ptr, u32 size);                                 // 0x002c4b30
    void  AsdMem_Free(void* ptr);                                           // 0x002c4360

    // Buffer blocks.  0x002C34A4 and 0x002BF798 are byte-identical 196-byte
    // bodies; they only differ in which arena literal their caller selects.
    void* AsdWork_Alloc(u32 a0, u32 a1, u32 a2, u32 size, u32 a4, u32 a5);  // 0x002c34a4
    void* AsdWork_Alloc2(u32 a0, u32 a1, u32 a2, u32 size, u32 a4, u32 a5); // 0x002bf798

    // String / file helpers
    void  UiText_Format(char* dst, const char* fmt, ...);                   // 0x002be7fc
    char* AsdString_Char(const char* s, int c);                             // 0x0010024c (Thumb)
    int   AsdMem_Compare(const void* a, const void* b, u32 len);            // 0x002b45f8
    void  AsdMem_Copy(void* dst, const void* src, u32 size);                // 0x002c5ff4
    void* AsdRes_Load(const char* name, u32* out_size, u32 flags);          // 0x002c32f0

    // AsdSDK heap-limit / GPU address helpers
    u32   AsdGpu_HeapStart();                                               // 0x002c3b98
    u32   AsdGpu_HeapSize();                                                // 0x002c3b88
    u32   AsdGpu_Address(const void* ptr);                                  // 0x002bc300
    void  AsdGpu_Lock(void* object);                                        // 0x002bf2b0 (`mov r0,r0`)
    f32   AsdGpu_ResolveFormat(u32 format, u32 param, u32* out_code);       // 0x002a6a24
    void  AsdGpu_SubmitCopy(const void* src, void* dst, u32 size);          // 0x002a69b0
    void  AsdGpu_Submit2D(u32 width, u32 height, const void* pixels);       // 0x00349a5c

    // Primitive builders
    u32   AsdPrim_VertexSize(const smt4::engine::AsdPrimRenderData* data);  // 0x00347380
    void  AsdGpu_Submit(void* queue,
                        const smt4::engine::AsdPrimUploadDesc* attr,
                        u32 address, u32 type);                             // 0x0023bb2c

    // AsdTMTexTable
    void* AsdMem_AllocFlags(u32 size, u32 flags);                           // 0x002b76e8

    // TMSprite binding helpers
    u32   UiTMSpr_func_0014f3fc(smt4::ui::AsdTMSpr* sprite);                // 0x0014f3fc
    void  UiTMSpr_func_0014f070(smt4::ui::AsdTMSpr* sprite, void* buffer);  // 0x0014f070
    void  UiTMSpr_func_0014f30c(smt4::ui::AsdTMSpr* sprite, void* buffer);  // 0x0014f30c
    void  UiTMSpr_func_0014f1cc(smt4::ui::AsdTMSpr* sprite, void* buffer);  // 0x0014f1cc
}

namespace {

using namespace smt4::engine;

u32 AsdAddr(const void* ptr)
{
    return static_cast<u32>(reinterpret_cast<std::uintptr_t>(ptr));
}

// The TMX/TGA loaders normalise every '\' in a directory string to '/'.
// 0x002C4E88..0x002C4EA4 (and the identical copy in 0x002C5B50) calls
// strchr from the advancing cursor, replaces the hit, then advances one byte.
void AsdTMTex_NormalizeSlashes(char* path)
{
    for (char* scan = path; *scan != '\0'; ++scan) {
        char* backslash = AsdString_Char(scan, '\\');
        if (backslash != nullptr)
            *backslash = '/';
    }
}

// 32-bit byte reversal matching the `rev` instruction used by the two
// palette-expansion paths in 0x0019FB58.
u32 AsdByteReverse(u32 value)
{
    return ((value & 0x000000FFu) << 24) |
           ((value & 0x0000FF00u) << 8)  |
           ((value & 0x00FF0000u) >> 8)  |
           ((value & 0xFF000000u) >> 24);
}

} // namespace

namespace smt4::engine {

AsdPrimState g_AsdPrimState{};              // 0x004DAEC0
AsdTMTexTableGlobal g_AsdTMTexTable{};      // 0x0044EA28

// ---------------------------------------------------------------------------
// AsdPrim (c:\SMT4\XRD686\AsdSDK\Source\Gfx\Prim\AsdPrim.cpp)
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x001042c8, 176)
void AsdPrim_func_001042c8(void* owner)
{
    for (u32 i = 0; i < 2; ++i) {
        // 0x00104310: AsdWork_Alloc(0x10000, 0x100, 0, owner, 0x10, 1)
        g_AsdPrimState.buffers[i] =
            AsdWork_Alloc(0x10000, 0x100, 0, AsdAddr(owner), 0x10, 1);
        // 0x00104324: `str r7,[r0,#8]` with r0 = base + i*4 and r7 = 0.
        reinterpret_cast<void**>(&g_AsdPrimState.field_08)[i] = nullptr;
    }

    g_AsdPrimState.field_10 = nullptr;      // 0x0010432c
    g_AsdPrimState.owner = owner;           // 0x00104330
}

// ---------------------------------------------------------------------------
// AsdMemory (c:\SMT4\XRD686\AsdSDK\Source\Sys\Mem\AsdMemory.cpp)
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x002c23f8, 56)
void* AsdMemory_func_002c23f8(u32 size)
{
    // 0x002c2410..0x002c2424: r0=r1=0x100, r2=0, r3=size, [sp]=1.
    return AsdMem_AllocAlign(0x100, 0x100, 0, size, 1);
}

// ---------------------------------------------------------------------------
// AsdTexture (c:\SMT4\XRD686\AsdSDK\Source\Gfx\Tex\AsdTexture.cpp)
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x002bd940, 172)
void* AsdTexture_func_002bd940(u32 kind)
{
    AsdTexture* texture;

    if (kind != 0) {
        // 0x002bd950: line 0x2B, r0=0x10000, zero flag 0.
        texture = reinterpret_cast<AsdTexture*>(
            AsdMem_AllocAlign(0x10000, 0x100, 0, 0x48, 0));
    } else {
        // 0x002bd97c: line 0x2F, r0=0x10000, zero flag 1.
        texture = reinterpret_cast<AsdTexture*>(
            AsdMem_AllocAlign(0x10000, 0x100, 0, 0x48, 1));
    }

    AsdMem_Zero(texture, 0x48);             // 0x002bd9ac

    texture->kind = 0x10000;                // 0x002bd9bc
    texture->format = 0xDE1;                // 0x002bd9c4
    texture->field_38 = 2;                  // 0x002bd9c8
    texture->field_3c = 0;                  // 0x002bd9c8
    texture->field_40 = 0;                  // 0x002bd9cc
    ++texture->ref_count;                   // 0x002bd9d0..0x002bd9d8

    return texture;
}

// DECOMP_FUNC(0x002bd730, 528)
void AsdTexture_func_002bd730(AsdTexture* texture)
{
    AsdGpu_Lock(texture);                   // 0x002bd738

    u32 address = AsdAddr(texture->data);   // 0x002bd73c
    u32 heap_start = AsdGpu_HeapStart();    // 0x002bd740
    u32 heap_size = AsdGpu_HeapSize();      // 0x002bd748

    // 0x002bd74c..0x002bd758: start <= address < start + size.  The failure
    // exit at 0x002bd908 simply pops; it leaves r0 holding the last compared
    // value (heap end, heap size or the masked bank), which no caller uses.
    if (address < heap_start || address >= heap_start + heap_size)
        return;

    // 0x002bd75c: 128-byte alignment of the source pointer.
    if ((address & 0x7Fu) != 0)
        return;

    // 0x002bd764..0x002bd778: both ends must stay in the same 0x02000000 bank.
    if ((address & 0xFE000000u) !=
        ((address + texture->data_size) & 0xFE000000u))
        return;

    u32 format_code = 0;
    f32 bytes_per_texel =
        AsdGpu_ResolveFormat(texture->format2, texture->param, &format_code);
    texture->gpu_format = format_code;      // 0x002bd784 stores through r2

    u32 pixel_count = texture->width * texture->height;
    u32 byte_size =
        static_cast<u32>(static_cast<f32>(pixel_count) * bytes_per_texel);

    // The binary emits the following block twice (0x002BD7CC and 0x002BD850).
    // The two copies are identical apart from the debug line numbers passed
    // to AsdMem_AllocAlign (0xB4/0xB8 versus 0xE3/0xE7).
    if (texture->format2 == 0x675A || texture->format2 == 0x675B) {
        if (texture->kind == 0x10000) {
            texture->gpu_address = AsdGpu_Address(texture->data);
            AsdGpu_Lock(reinterpret_cast<void*>(
                static_cast<std::uintptr_t>(texture->gpu_address)));
            return;
        }

        texture->converted = nullptr;       // 0x002bd7dc
        if (texture->kind == 0x20000) {
            texture->converted = AsdMem_AllocAlign(0x20000, 0x100, 0,
                                                   byte_size, 1);
        } else if (texture->kind == 0x30000) {
            texture->converted = AsdMem_AllocAlign(0x30000, 0x100, 0,
                                                   byte_size, 1);
        }

        // 0x002bd8cc: queue a copy from the file buffer to the converted one.
        AsdGpu_SubmitCopy(texture->data, texture->converted, byte_size);
        texture->gpu_address = AsdGpu_Address(texture->converted);
        AsdGpu_Lock(reinterpret_cast<void*>(
            static_cast<std::uintptr_t>(texture->gpu_address)));
        return;
    }

    if (texture->kind == 0x10000) {
        texture->gpu_address = AsdGpu_Address(texture->data);
        AsdGpu_Lock(reinterpret_cast<void*>(
            static_cast<std::uintptr_t>(texture->gpu_address)));
        return;
    }

    texture->converted = nullptr;           // 0x002bd860
    if (texture->kind == 0x20000) {
        texture->converted = AsdMem_AllocAlign(0x20000, 0x100, 0,
                                               byte_size, 1);
    } else if (texture->kind == 0x30000) {
        texture->converted = AsdMem_AllocAlign(0x30000, 0x100, 0,
                                               byte_size, 1);
    }

    AsdGpu_SubmitCopy(texture->data, texture->converted, byte_size);
    texture->gpu_address = AsdGpu_Address(texture->converted);
    AsdGpu_Lock(reinterpret_cast<void*>(
        static_cast<std::uintptr_t>(texture->gpu_address)));
}

// ---------------------------------------------------------------------------
// AsdTexTMX (c:\SMT4\XRD686\AsdSDK\Source\Gfx\Tex\AsdTexTMX.cpp)
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x0019fb58, 756)
void AsdTexTMX_func_0019fb58(AsdTexture* texture, const AsdTMXHeader* tmx,
                             u32 unused, u32 texture_kind)
{
    (void)unused;

    const u32 width = tmx->width;
    const u32 height = tmx->height;

    // `sb` is the four-byte palette-entry size: shifted by 4 it advances past
    // a 16-colour palette, shifted by 8 past a 256-colour palette.
    const u32 palette_entry_size = 4;

    // [sp+8].  The `field_11 != 0` path in the binary reads this slot without
    // ever storing it; the model starts it at null so the path is defined.
    u32* pixels = nullptr;

    if (tmx->field_11 == 0) {
        texture->data_size = width * height * 4u;       // 0x0019fb8c
        pixels = reinterpret_cast<u32*>(
            AsdMem_Alloc(0x100, 0x100, 0, texture->data_size, 1));
    }

    const u8* palette = reinterpret_cast<const u8*>(tmx) + 0x40;

    if (tmx->format == 0x14 || tmx->format == 0x24 || tmx->format == 0x2C) {
        // 4-bit indices.  0x0019FBF0..0x0019FC80: bottom-up rows, two pixels
        // per unrolled step, palette alpha doubled while alpha < 0x7F.
        const u8* texels = palette + palette_entry_size * 16u;

        for (u32 y = 0; y < height; ++y) {
            const u32 row_base = (height - y - 1u) * width;
            u32* out = pixels + y * width;

            for (u32 x = 0; x < width; ++x) {
                // 0x0019FC20 computes `(row_base + x)` and 0x0019FC30 reads
                // `ldrb [fp, r2, asr #1]`: the nibble stream is continuous
                // across rows, which matters for odd widths.
                u8 packed = texels[(row_base + x) >> 1];
                u32 index = (x & 1u) != 0 ? (packed >> 4) : (packed & 0x0Fu);
                u32 color = reinterpret_cast<const u32*>(palette)[index];
                u32 alpha = color >> 24;

                // 0x0019FC44..0x0019FC58.
                alpha = alpha < 0x7Fu ? ((alpha << 1) & 0xFFu) : 0xFFu;
                out[x] = (AsdByteReverse(color) & 0xFFFFFF00u) | alpha;
            }
        }
    } else if (tmx->format == 0x13 || tmx->format == 0x1B) {
        // 8-bit indices.  0x0019FC84: a 256-entry LUT is built from the
        // palette (bits 3 and 4 of the index are swapped) and then applied
        // bottom-up.
        u32* lut = reinterpret_cast<u32*>(
            AsdMem_Alloc(0x100, 0x100, 0, 0x400, 1));

        for (u32 i = 0; i < 0x100u; ++i) {
            u32 index = (i & 0xE7u) | ((i & 0x10u) >> 1) | ((i & 8u) << 1);
            u32 color = reinterpret_cast<const u32*>(palette)[index];
            u32 b = color & 0xFFu;
            u32 g = (color >> 8) & 0xFFu;
            u32 r = (color >> 16) & 0xFFu;
            u32 a = color >> 24;

            // 0x0019FCE0..0x0019FD04.
            a = a < 0x7Fu ? ((a << 1) & 0xFFu) : 0xFFu;
            lut[i] = (b << 24) | (g << 16) | (r << 8) | a;
        }

        // 0x0019FD20: pixel base minus one, so the paired reads land on the
        // first byte of the row.
        const u8* texels = palette + palette_entry_size * 0x100u;

        for (u32 y = 0; y < height; ++y) {
            const u8* row = texels + (height - y - 1u) * width;
            u32* out = pixels + y * width;

            for (u32 x = 0; x < width; ++x)
                out[x] = lut[row[x]];
        }

        AsdMem_Free(lut);                   // 0x0019FD94
    }

    // 0x0019FD9C..0x0019FDF8: publish metadata, allocate the GPU work
    // buffer, then upload width x height texels.
    texture->kind = texture_kind;           // +0x08, `ldr r0,[sp,#0x18]`
    texture->format = 0xDE1;                // +0x04
    texture->format2 = 0x6752;              // +0x1C
    texture->param = 0x1401;                // +0x20
    texture->width = width;                 // +0x14
    texture->height = height;               // +0x18

    texture->data = AsdWork_Alloc(0x10000, 0x100, 0,
                                  texture->data_size, 0x80, 1);  // +0x24
    AsdGpu_Submit2D(width, height, pixels); // 0x0019FDFC
    AsdMem_Free(pixels);                    // 0x0019FE0C tail call
}

// ---------------------------------------------------------------------------
// AsdTexTGA (c:\SMT4\XRD686\AsdSDK\Source\Gfx\Tex\AsdTexTGA.cpp)
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x00257e6c, 436)
void AsdTexTGA_func_00257e6c(AsdTexture* texture, const AsdTGAHeader* tga,
                             const void* unused, u32 texture_kind)
{
    (void)unused;

    // 0x00257e80: memcmp(data + 0x12, "NW4C_Tga Ver1.0", 0x10).
    if (AsdMem_Compare(tga->signature, "NW4C_Tga Ver1.0", 0x10) != 0)
        return;

    const u32 height = tga->height;         // 0x00257e9c..0x00257ec0
    const u32 width = tga->width;

    texture->height = height;               // +0x18
    texture->width = width;                 // +0x14
    texture->kind = texture_kind;           // +0x08 from r3
    texture->format = 0xDE1;                // +0x04

    // 0x00257ED0: unaligned `ldr r0,[r6,#0x10]` with r6 = data + 0x12, i.e. a
    // little-endian word at +0x22.  Assembled byte-wise because a u32 member
    // would be aligned to +0x24 by the ABI.
    const u8* header_bytes = reinterpret_cast<const u8*>(tga);
    const u32 chunk_offset =
        static_cast<u32>(header_bytes[0x22]) |
        (static_cast<u32>(header_bytes[0x23]) << 8) |
        (static_cast<u32>(header_bytes[0x24]) << 16) |
        (static_cast<u32>(header_bytes[0x25]) << 24);

    const u8* chunk = header_bytes + chunk_offset;

    for (;;) {
        // 0x00257EF8: `nw4c_txd` carries the raw pixel payload.
        if (AsdMem_Compare(chunk, "nw4c_txd", 8) == 0) {
            const u32 size = reinterpret_cast<const AsdTGABlock*>(chunk)->size;
            const u8* payload = chunk + 0x0C;

            texture->data_size = size - 0x0Cu;              // +0x28
            texture->data = AsdWork_Alloc2(0x10000, 0x100, 0,
                                           texture->data_size, 0x80, 1);
            AsdMem_Copy(texture->data, payload, texture->data_size);
        }

        // 0x00257F50: `nw4c_tfm` selects the ETC1 texture format.
        if (AsdMem_Compare(chunk, "nw4c_tfm", 8) == 0) {
            const u32 size = reinterpret_cast<const AsdTGABlock*>(chunk)->size;
            u8 name[8] = {};

            // The binary copies the whole tfm payload into an eight-byte
            // stack buffer and compares only the first eight bytes.  Clamp
            // the copy to the buffer instead of reproducing that overflow;
            // only those first eight bytes affect the result.
            u32 copy_size = size > 0x0Cu ? size - 0x0Cu : 0u;
            if (copy_size > sizeof(name))
                copy_size = sizeof(name);
            AsdMem_Copy(name, chunk + 0x0C, copy_size);

            // 0x00409540: the binary compares eight bytes against
            // "Etc1\0\0\0\0", not the five-byte literal alone.
            static const u8 kEtc1Name[8] = { 'E', 't', 'c', '1', 0, 0, 0, 0 };

            if (AsdMem_Compare(name, "Etc1_a4", 8) == 0) {
                texture->param = 0x1401;        // +0x20, 0x00257F9C
                texture->format2 = 0x675B;      // +0x1C, 0x00257FA0
            } else if (AsdMem_Compare(name, kEtc1Name, 8) == 0) {
                texture->format2 = 0x675A;      // +0x1C, 0x00257FC4
                texture->param = 0x1401;        // +0x20
            }
        }

        // 0x00257FD0: `nw4c_end` terminates the chain; anything else advances
        // by the child block size.
        if (AsdMem_Compare(chunk, "nw4c_end", 8) == 0)
            break;

        chunk += reinterpret_cast<const AsdTGABlock*>(chunk)->size;
    }
}

// ---------------------------------------------------------------------------
// AsdTMTexTable (c:\SMT4\XRD686\AsdSDK\Source\Gfx\AsdTexManager\AsdTMTexTable.cpp)
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x002c4e28, 620)
void* AsdTMTexTable_func_002c4e28(u32 group_id)
{
    void* table = AsdTMTexTable_func_002c5b04(group_id, 0);  // 0x002c4e38

    if (table == nullptr)
        return nullptr;

    AsdTMTexGroupEntry* entry = &g_AsdTMTexTable.groups[group_id];

    // 0x002c4e58: the .tgd group is loaded only once.
    if (entry->group != nullptr)
        return table;

    char path[0x80];
    char filename[0x100];

    AsdString_Strcpy(path, g_AsdTMTexTable.paths->root);       // 0x002c4e70
    AsdTMTex_NormalizeSlashes(path);
    AsdString_Strcpy(g_AsdTMTexTable.paths->root, path);       // 0x002c4eb0

    // 0x002c4ecc: "%s%s%s.%s" with root, group name, "GroupTable", "tgd".
    UiText_Format(filename, "%s%s%s.%s",
                  g_AsdTMTexTable.paths->root, entry->name,
                  "GroupTable", "tgd");

    u32 file_size = 0;
    const u8* file = reinterpret_cast<const u8*>(
        AsdRes_Load(filename, &file_size, 0));               // 0x002c4ee0

    if (file == nullptr)
        return table;

    // 0x002c4f14: eight-byte group context.
    AsdTMTexGroup* group = reinterpret_cast<AsdTMTexGroup*>(
        AsdMem_Alloc(0x100, 0x100, 0, 8, 1));
    entry->group = group;

    group->header = reinterpret_cast<AsdTMTexGroupHeader*>(
        AsdMem_Alloc(0x100, 0x100, 0, 0x40, 1));             // 0x002c4f3c
    AsdMem_Copy(group->header, file, 0x40);                  // 0x002c4f58..0x002c4f6c

    const u8* record_data = file + 0x40;
    AsdTMTexGroupRecord* previous = nullptr;

    for (s32 i = 0; i < group->header->record_count; ++i) {
        AsdTMTexGroupRecord* record = reinterpret_cast<AsdTMTexGroupRecord*>(
            AsdMem_Alloc(0x100, 0x100, 0, 0x14, 1));         // 0x002c4fa4

        record->field_00 = record_data[0];                   // 0x002c4fa8
        record->item_count = record_data[4];                 // 0x002c4fb8
        record->field_08 = record_data[8];                   // 0x002c4fc8

        if (record->item_count > 0) {
            const u32 item_bytes = record->item_count * 5u * 4u;
            record->items = AsdMem_Alloc(0x100, 0x100, 0, item_bytes, 1);
            // 0x002c5020: memcpy of item_count * 20 bytes from record + 0xC.
            AsdMem_CopyLarge(record->items, record_data + 0x0C, item_bytes);
        } else {
            record->items = nullptr;                         // 0x002c4fcc
        }

        // 0x002c503c / 0x002c5044: first record hangs off the context, the
        // rest are chained through +0x10.
        if (previous == nullptr)
            group->first = record;
        else
            previous->next = record;
        previous = record;

        // 0x002c5034: cursor advance = 0xC + item_count * 20.
        record_data += 0x0C + record->item_count * 5u * 4u;
    }

    AsdMem_Free(const_cast<u8*>(file));                      // 0x002c505c
    return table;
}

// DECOMP_FUNC(0x002c5b04, 652)
void* AsdTMTexTable_func_002c5b04(u32 group_id, u32 flags)
{
    AsdTMTexGroupEntry* entry = &g_AsdTMTexTable.groups[group_id];

    // 0x002c5b20: return the cached table.
    if (entry->table != nullptr)
        return entry->table;

    char path[0x80];
    char filename[0x100];

    AsdString_Strcpy(path, g_AsdTMTexTable.paths->root);       // 0x002c5b38
    AsdTMTex_NormalizeSlashes(path);
    AsdString_Strcpy(g_AsdTMTexTable.paths->root, path);       // 0x002c5b78

    // 0x002c5b94: "%s%s.%s" with root, group name, "ttd".
    UiText_Format(filename, "%s%s.%s",
                  g_AsdTMTexTable.paths->root, entry->name, "ttd");

    u32 file_size = 0;
    const u8* file = reinterpret_cast<const u8*>(
        AsdRes_Load(filename, &file_size, flags & 3u));      // 0x002c5bb4

    if (file == nullptr) {
        entry->table = nullptr;                              // 0x002c5bc0
        return nullptr;
    }

    const AsdTMTexFile* header = reinterpret_cast<const AsdTMTexFile*>(file);
    u8* nodes = const_cast<u8*>(file) + header->node_offset;
    AsdTMTexEntry* entries = reinterpret_cast<AsdTMTexEntry*>(
        const_cast<u8*>(file) + header->entry_offset);
    AsdTMTexRef* refs = reinterpret_cast<AsdTMTexRef*>(
        const_cast<u8*>(file) + header->ref_offset);
    const u8* payload = file + header->data_offset;

    // 0x002c5bfc: resolve node indices (stride 0x50) or clear 0xFFFFFFFF.
    for (s32 i = 0; i < header->entry_count; ++i) {
        u32 node = entries[i].node_offset;

        if (node == 0xFFFFFFFFu)
            entries[i].node_offset = 0;
        else
            entries[i].node_offset =
                AsdAddr(nodes + node * sizeof(AsdTMTexNode));
    }

    // 0x002c5c40: resolve the two pointers of every 16-byte reference.
    for (s32 i = 0; i < header->ref_count; ++i) {
        AsdTMTexRef* ref = refs + i;
        ref->node_index =
            AsdAddr(reinterpret_cast<u8*>(entries) +
                    ref->node_index * sizeof(AsdTMTexEntry));
        ref->data_offset = AsdAddr(payload + ref->data_offset);
    }

    // 0x002c5c80: 0x2C-byte table header.
    AsdTMTexTable* table = reinterpret_cast<AsdTMTexTable*>(
        AsdMem_AllocFlags(0x2C, flags));

    if (header->ref_count <= 0) {
        table->entries = nullptr;                            // 0x002c5c94
    } else {
        // 0x002c5cb4: count * 0x20 bytes of 0x20-byte descriptors.
        table->entries = reinterpret_cast<AsdTMTexTableEntry*>(
            AsdMem_AllocFlags(static_cast<u32>(header->ref_count) * 0x20u,
                              flags));
    }

    // 0x002c5cd0: every descriptor points back at the table and at its
    // 16-byte reference record (r5 advances by 0x10, the descriptor by 0x20).
    for (s32 i = 0; i < header->ref_count; ++i) {
        table->entries[i].owner = table;
        table->entries[i].record = refs + i;
    }

    table->file = const_cast<u8*>(file);                     // +0x04
    table->file_alt = const_cast<u8*>(file);                 // +0x08

    // 0x002c5cf8..0x002c5d54: normalise the sub-directory and append the
    // file-relative name from `file + 4`.
    char* base = g_AsdTMTexTable.paths->base;
    AsdString_Strcpy(path, base);
    AsdTMTex_NormalizeSlashes(path);
    AsdString_Strcpy(base, path);
    UiText_Format(table->path, "%s%s/", base,
                  reinterpret_cast<const char*>(file) + 4);

    entry->table = table;                                    // 0x002c5d60
    return table;
}

// ---------------------------------------------------------------------------
// AsdPrimRenderData (c:\SMT4\XRD686\AsdSDK\Source\Gfx\Prim\AsdPrimRenderData.cpp)
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x00346db0, 992)
void AsdPrimRenderData_func_00346db0(AsdPrimRenderData* data)
{
    // [sp+0x18], [sp+0x10] and [sp+0x08]: each descriptor starts with the
    // four bytes { 0, 1, 0xFF, 0xFF } and carries a zero word at +0x04.
    AsdPrimUploadDesc attr_18 = { { 0, 1, 0xFF, 0xFF }, 0u };
    AsdPrimUploadDesc attr_10 = { { 0, 1, 0xFF, 0xFF }, 0u };
    AsdPrimUploadDesc attr_08 = { { 0, 1, 0xFF, 0xFF }, 0u };

    const u32 flags = data->flags;

    // 0x00346E04..0x00346E84: one vertex-stream allocation sized by
    // 0x00347380 (flags bits 0,1,2,3,4,5 select 12/16/8/12/12/4 bytes).
    if ((flags & 0x100u) != 0) {
        data->buffer = AsdWork_Alloc(0x10000, 0x100, 0,
                                     AsdPrim_VertexSize(data), 0x10, 1);
    } else {
        data->buffer = AsdWork_Alloc(0x100, 0x100, 0,
                                     AsdPrim_VertexSize(data), 0x10, 1);
    }

    u32 cursor = 0;                         // r5

    // 0x00346E90: stream 0 -- positions, three floats per vertex.
    if ((flags & 1u) != 0) {
        data->positions = data->buffer;                 // +0x30
        cursor = data->vertex_count * 3u * 4u;

        if ((flags & 0x100u) != 0) {
            attr_18.rgba[2] = 0;                        // `strb r6,[sp,#0x1a]`
            u32 address = AsdGpu_Address(data->positions);
            AsdGpu_Submit(data->command_queue, &attr_18, address, 0x0B);
        }
    }

    // 0x00346ED4: stream 1 -- four floats per vertex, all 1.0f.
    if ((flags & 2u) != 0) {
        data->uv = reinterpret_cast<u8*>(data->buffer) + cursor;  // +0x34
        u32 float_count = data->vertex_count * 4u;
        f32* values = reinterpret_cast<f32*>(data->uv);

        for (u32 i = 0; i < float_count; ++i)
            values[i] = 1.0f;                           // 0x00346F04

        cursor += data->vertex_count * 0x10u;

        if ((flags & 0x100u) != 0) {
            attr_08.rgba[2] = 1;                        // `strb r8,[sp,#0xa]`
            u32 address = AsdGpu_Address(data->uv);
            AsdGpu_Submit(data->command_queue, &attr_08, address, 0x0F);
        }
    }

    // 0x00346F6C: stream 2 -- one byte per component, 0xFF-filled (four
    // components per vertex).
    if ((flags & 0x20u) != 0) {
        data->colors = reinterpret_cast<u8*>(data->buffer) + cursor;  // +0x38
        u32 byte_count = data->vertex_count * 4u;
        u8* values = reinterpret_cast<u8*>(data->colors);

        for (u32 i = 0; i < byte_count; ++i)
            values[i] = 0xFF;                           // 0x00346FAC

        cursor += data->vertex_count * 4u;

        if ((flags & 0x100u) != 0) {
            attr_08.rgba[2] = 1;                        // 0x00346FD8
            u32 address = AsdGpu_Address(data->colors);
            AsdGpu_Submit(data->command_queue, &attr_08, address, 0x0D);
        }
    }

    // 0x00346FF8: stream 3 -- no cursor advance in the binary.
    if ((flags & 4u) != 0) {
        data->indices = reinterpret_cast<u8*>(data->buffer) + cursor; // +0x3C

        if ((flags & 0x100u) != 0) {
            attr_10.rgba[2] = 2;                        // `strb r0,[sp,#0x12]`
            u32 address = AsdGpu_Address(data->indices);
            AsdGpu_Submit(data->command_queue, &attr_10, address, 7);
        }
    }

    // 0x00347040..0x003470AC: 16-bit index buffer, two bytes per index.
    if ((flags & 0x100u) != 0) {
        data->index_buffer = AsdWork_Alloc2(0x10000, 0x100, 0,
                                            data->index_count * 2u, 0x10, 1);
    } else {
        data->index_buffer = AsdWork_Alloc2(0x100, 0x100, 0,
                                            data->index_count * 2u, 0x10, 1);
    }

    // 0x003470B0..0x00347110: every index is cleared to zero (the binary
    // handles an odd leading index and then writes pairs).
    u16* indices = reinterpret_cast<u16*>(data->index_buffer);
    for (u32 i = 0; i < data->index_count; ++i)
        indices[i] = 0;

    // 0x00347114: cache the GPU address and count of the index buffer.
    if ((flags & 0x100u) != 0) {
        data->index_address = AsdGpu_Address(data->index_buffer);
        data->index_address_count = data->index_count;
        data->index_uploaded = 0;
    }
}

// ---------------------------------------------------------------------------
// AsdTMSpr (c:\SMT4\XRD686\AsdSDK\Source\Gfx\AsdTexManager\AsdTMSpr.cpp)
// ---------------------------------------------------------------------------

} // namespace smt4::engine

namespace smt4::ui {

// DECOMP_FUNC(0x00144fbc, 416)
void* AsdTMSpr_func_00144fbc(AsdTMSpr* sprite, u32 flags,
                             u32 alignment, u32 unused)
{
    (void)unused;

    // The returned slot starts out as r5 = sprite (0x00144fd4) and is only
    // cleared after the buffer-size probe succeeds.
    void* result = sprite;

    const u32 kind = static_cast<u32>(sprite->type) & 0xF0u;

    if (kind != 0x10u && kind != 0x20u && kind != 0x30u)
        return result;

    // 0x00144FF0: returns the byte size to reserve for this sprite kind.
    const u32 buffer_bytes = UiTMSpr_func_0014f3fc(sprite);
    if (buffer_bytes == 0)
        return result;

    result = nullptr;

    if ((flags & 1u) != 0) {
        if ((flags & 2u) != 0) {
            // 0x00145010: 64 KiB arena, zero flag 0.
            result = AsdWork_Alloc2(0x10000, 0x100, 0,
                                    buffer_bytes, alignment, 0);
        } else {
            // 0x00145048: 64 KiB arena, zero flag 1.
            result = AsdWork_Alloc2(0x10000, 0x100, 0,
                                    buffer_bytes, alignment, 1);
        }
    } else {
        if ((flags & 2u) != 0) {
            // 0x00145080: 256-byte arena, zero flag 0.
            result = AsdWork_Alloc2(0x100, 0x100, 0,
                                    buffer_bytes, alignment, 0);
        } else {
            // 0x001450B4: 256-byte arena, zero flag 1.
            result = AsdWork_Alloc2(0x100, 0x100, 0,
                                    buffer_bytes, alignment, 1);
        }
    }

    // 0x001450DC: bind by the object's high-nibble type.
    if (kind == 0x10u)
        UiTMSpr_func_0014f070(sprite, result);
    else if (kind == 0x20u)
        UiTMSpr_func_0014f30c(sprite, result);
    else if (kind == 0x30u)
        UiTMSpr_func_0014f1cc(sprite, result);

    AsdMem_Free(sprite);                    // 0x00145138
    return result;
}

} // namespace smt4::ui
