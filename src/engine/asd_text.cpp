#include "engine/asd_text.h"
#include "engine/asd_symbols.h"

// ---------------------------------------------------------------------------
// Observed call targets (addresses are the branch targets in code.bin)
// ---------------------------------------------------------------------------

extern "C" {
    // CRT / memory
    void  Crt_SetEncoding(s32 mode, const char* name);                      // 0x00100238
    void* AsdMem_Alloc(u32 a0, u32 a1, u32 a2, u32 size, u32 flag);         // 0x002c4b84
    void* AsdMem_AllocAlign(u32 a0, u32 a1, u32 a2, u32 size, u32 flag);    // 0x002c54f0
    void  AsdMem_Zero(void* ptr, u32 size);                                 // 0x002c4b30
    void  AsdMem_Free(void* ptr);                                           // 0x002c4360
    void  AsdRef_Dec(void* object);                                         // 0x002c0a6c
    void* AsdRef_Get(void* handle);                                         // 0x002c0ac8

    // AsdFont
    smt4::engine::AsdFontEntry* AsdFont_GetEntry(u32 index);                // 0x002aed40
    void* AsdFont_CreateInfo();                                             // 0x00121d58
    int   AsdFont_Parse(smt4::engine::AsdFontInfo* info, const void* data);  // 0x00121b80
    void* AsdFont_GetGlyph(smt4::engine::AsdFontEntry* entry, u32 code);    // 0x00248130
    void* AsdTexture_Create(u32 kind);                                      // 0x002bd940
    void* AsdTexture_Finalize(void* texture);                               // 0x002bd730

    // AsdText
    int   AsdText_IsControlCode(u32 code);                                  // 0x002ae6b0
    u32   AsdText_Utf8ToCodes(const char* src, u16* dst, u32 mode);         // 0x001eb498
    u32   AsdText_SerializeCodes(const u16* src, u16* dst, u32 mode);       // 0x002d602c
    u8*   AsdText_ConvertName(u8* dst, u32 size, const char* src,
                              u32* state);                                  // 0x002b2574 (Thumb)
    int   AsdText_UpdateLayout(smt4::engine::AsdText* text);                // 0x002b3398
    void  AsdText_ClearGlobalState();                                       // 0x00210878

    // AsdListBox / UI
    void* AsdList_func_002b2814(void* list, void* item, void* callback);    // 0x002b2814
    smt4::ui::AsdListBoxItem* AsdListBox_FindItem(void* handle, u32 id);    // 0x00254ff0
    void  AsdListBox_Relayout(void* handle);                                // 0x00259d88
    void  AsdListBox_AdvanceCounter(void* field);                           // 0x002d567c
    int   AsdUi_IsRegistered(void* handle);                                 // 0x002bf41c
    void  AsdText_ResetGlobals();                                           // 0x002bc2c4
    void  AsdScriptText_SetChannels(void* obj, u32 a1, u32 a2, f32 value);  // 0x002bda00
    void  AsdScriptText_SetColor(void* obj, u32 color);                     // 0x002bda10
    void* AsdScriptText_Create(u32 index);                                  // 0x002bda1c
    void  AsdScriptText_SetPlacement(void* obj, u32 a1, u32 a2, f32 value); // 0x001182c0
    // The 0x002C3344 / 0x002C32F8 layout helpers are declared canonically as
    // UiSpriteGroup_Init / UiSpriteGroup_BindTable in engine/asd_symbols.h.
    void  AsdLayout_Setup(void* block, s32 a1, s32 a2);                     // 0x00296f18
    void  AsdLayout_SetupSlots(void* block, u8 a1, u8 a2, u8 a3, u8 a4);    // 0x00296ef8
}

// Scratch buffers used by the two-pass code conversion in
// AsdText_func_00286c5c: UTF-8 -> intermediate (0x004DAF08) -> big-endian
// usable code buffer (0x004DCF08).
extern u16 g_AsdTextDecodeBuffer[];         // 0x004DAF08
extern u16 g_AsdTextCodeBuffer[];           // 0x004DCF08

// Control-code expansion tables (8 entries each).
extern void* g_AsdTextCodeTable[8];         // 0x004DAEE8
extern u16 g_AsdTextCodeChars[8];           // 0x004DEF18
extern s32 g_AsdTextCodeCounts[8];          // 0x004DEF28

namespace smt4::engine {

AsdFontManager g_AsdFontManager{};          // 0x00464A70
AsdTextCodes g_AsdTextCodes{};              // 0x00464D48

// These short entry points mutate still-unidentified words in the shared
// text-code table. Keep the base opaque so ARM codegen retains the original
// shared literal and field displacement.
// DECOMP_FUNC(0x0010af38, 16)
void AsdText_SetCodeField14(u32 val) {
    auto* codes = reinterpret_cast<volatile AsdTextCodes*>(0x00464D48);
    asm volatile("" : "+r"(codes));
    codes->field_14 = val;
}

// DECOMP_FUNC(0x0010a6fc, 16)
void AsdText_SetCodeField1C(u32 val) {
    auto* codes = reinterpret_cast<volatile AsdTextCodes*>(0x00464D48);
    asm volatile("" : "+r"(codes));
    codes->field_1c = val;
}

// DECOMP_FUNC(0x0010b340, 16)
void AsdText_SetCodeField30(u32 val) {
    auto* codes = reinterpret_cast<volatile AsdTextCodes*>(0x00464D48);
    asm volatile("" : "+r"(codes));
    codes->field_30 = val;
}
// DECOMP_FUNC(0x0010a588, 152)


// ---------------------------------------------------------------------------
// AsdFont
// ---------------------------------------------------------------------------

//
__attribute__((naked)) void AsdFont_func_0010a588(s32)
{
    asm volatile(
        "push {r3, r4, r5, lr}\n"
        "mov r4, r0\n"
        "add r1, pc, #0x44\n"
        "mov r0, #2\n"
        ".word 0xfaffd726\n"
        "ldr r5, [pc, #0x40]\n"
        "mov r0, #0x2c\n"
        "ldr r1, [pc, #0x3c]\n"
        "str r4, [r5, #4]\n"
        "mul r4, r4, r0\n"
        "add r0, pc, #0x34\n"
        "mov r0, r0\n"
        "mov r0, #1\n"
        "mov r1, #0x100\n"
        "str r0, [sp]\n"
        "mov r3, r4\n"
        "mov r2, #0\n"
        "mov r0, r1\n"
        ".word 0xeb06ebc6\n"
        "str r0, [r5]\n"
        "pop {r3, r4, r5, pc}\n"
        ".word 0x53494a53\n" // "SJIS"
        ".word 0x00000000\n"
        ".word 0x00464a70\n" // g_AsdFontManager
        ".word 0x00000269\n"
        ".word 0x535c3a63\n" // AsdFont.cpp source path
        ".word 0x5c34544d\n"
        ".word 0x36445258\n"
        ".word 0x415c3638\n"
        ".word 0x44536473\n"
        ".word 0x6f535c4b\n"
        ".word 0x65637275\n"
        ".word 0x7866475c\n"
        ".word 0x6e6f465c\n"
        ".word 0x73415c74\n"
        ".word 0x6e6f4664\n"
        ".word 0x70632e74\n"
        ".word 0x00000070\n");
}

// DECOMP_FUNC(0x002c4710, 1004)
int AsdFont_func_002c4710(u32 index, const void* data)
{
    // 0x002c4718: `ldr r1,[r1]` / `ldr r1,[r1,#4]` with the count compared
    // unsigned (`bls` = count <= index).
    if (g_AsdFontManager.entries == nullptr || g_AsdFontManager.count <= index)
        return 0;

    AsdFontEntry* entry = (AsdFontEntry*)((u8*)g_AsdFontManager.entries
                                          + index * 0x2C);
    if (entry == nullptr)
        return 0;

    if (entry->resource != nullptr) {
        if (entry->textures != nullptr) {
            for (u32 i = 0; i < entry->texture_count; ++i) {
                AsdFontTexture* texture = entry->textures[i];
                texture->data = nullptr;            // `str r8,[r0,#0x24]`
                AsdRef_Dec(texture);                // 0x002c0a6c
            }
            AsdMem_Free(entry->textures);           // 0x002c4360
            entry->textures = nullptr;
        }
        if (entry->info != nullptr) {
            // Virtual slot +0x04 of the info object (0x002c47ac/0x002c47b4).
            void** vtable = *(void***)entry->info;
            ((void (*)(AsdFontInfo*))vtable[1])(entry->info);
            entry->info = nullptr;
        }
        if (entry->resource != nullptr) {
            AsdMem_Free(entry->resource);
            entry->resource = nullptr;
        }
        entry->chunk = nullptr;                     // `str r8,[r4,#4]`
    }

    entry->resource = const_cast<void*>(data);

    void* info = AsdMemory_func_002c23f8(0x18);
    if (info != nullptr)
        info = AsdFont_CreateInfo();                // 0x00121d58
    entry->info = (AsdFontInfo*)info;

    // 0x002c47f8: a zero parse result ends the routine early with success.
    if (AsdFont_Parse(entry->info, entry->resource) == 0)
        return 1;

    // Linear scan for the chunk tagged "FINF" (0x464E4946), stride from the
    // word at +0x04.  ARM tests the tag additively (`adds r5,r5,#0xb9b1b6ba`;
    // zero means 0x464E4946).  The surviving pointer is cursor + 8
    // (0x002c483c).
    u8* cursor = (u8*)entry->resource + *(u16*)((u8*)entry->resource + 6);
    u32 chunk_count = *(u16*)((u8*)entry->resource + 0x10);
    u8* found = nullptr;
    for (u32 i = 0; i < chunk_count; ++i) {
        u32 tag = *(u32*)cursor;
        u32 next = *(u32*)(cursor + 4);
        if (tag == 0x464E4946)
            found = cursor + 8;
        cursor += next;
    }
    entry->chunk = found;

    // 0x002c4850: no null check before dereferencing found + 8.
    AsdFontHeader* header =
        *(AsdFontHeader**)(found + 8);

    entry->textures = (AsdFontTexture**)AsdMem_AllocAlign(
        0x100, 0x100, 0, (u32)header->glyph_count * 4, 1);
    entry->texture_count = header->glyph_count;
    entry->field_28 = 0.0f;
    entry->format = header->format;

    // 12-entry jump table at 0x002C48A8.  Entries 6, 7, 10 and the default
    // (format >= 12) share the four-instruction body at 0x002C4A7C.
    switch (header->format) {
    case 0:
        entry->field_18 = 0x6752;
        entry->field_1c = 0x1401;
        entry->field_20 = 0x20;
        break;
    case 1:
        entry->field_18 = 0x6754;
        entry->field_1c = 0x1401;
        entry->field_20 = 0x18;
        break;
    case 2:
        entry->field_18 = 0x6752;
        entry->field_1c = 0x8034;
        entry->field_20 = 0x10;
        break;
    case 3:
        entry->field_18 = 0x6754;
        entry->field_1c = 0x8363;
        entry->field_20 = 0x10;
        break;
    case 4:
        entry->field_18 = 0x6752;
        entry->field_1c = 0x8033;
        entry->field_20 = 0x10;
        break;
    case 5:
        entry->field_18 = 0x6758;
        entry->field_1c = 0x1401;
        entry->field_20 = 0x10;
        break;
    case 8:
        entry->field_18 = 0x6756;
        entry->field_1c = 0x1401;
        entry->field_20 = 0x08;
        break;
    case 9:
        entry->field_18 = 0x6758;
        entry->field_1c = 0x6758 + 8;   // `add r1,r2,#8` with r2=0x6758
        entry->field_20 = 0x08;
        break;
    case 11:
        entry->field_18 = 0x6756;
        entry->field_1c = 0x6756 + 0x0B; // `add r1,r2,#0xb` with r2=0x6756
        entry->field_20 = 0x04;
        break;
    case 6:
    case 7:
    case 10:
    default:
        entry->field_18 = 0x6756;
        entry->field_1c = 0x1401;
        entry->field_20 = 0;
        // 0x002c4a7c stores the three words then branches straight to
        // 0x002c4a74 (`mov r0,#1`), skipping the encoding byte and the
        // texture loop.
        return 1;
    }

    // 0x002c49d8: `sub r0,r2,#0x6700; subs r0,r0,#0x56` == compare with 0x6756.
    entry->encoding = (entry->field_18 == 0x6756) ? 2 : 1;

    u32 offset = 0;
    for (u32 i = 0; i < entry->texture_count; ++i) {
        AsdFontTexture* texture = (AsdFontTexture*)AsdTexture_Create(0);
        entry->textures[i] = texture;

        texture->field_04 = 0xDE1;
        texture->field_08 = 0x10000;
        texture->field_0c = 0x2000000;
        texture->field_10 = 0;
        texture->width = header->width;
        texture->height = header->height;
        texture->field_1c = entry->field_18;
        texture->field_20 = entry->field_1c;
        texture->data = (u8*)header->glyph_data + offset;
        texture->field_28 = header->glyph_stride;

        AsdTexture_Finalize(texture);

        offset += header->glyph_stride;
    }

    return 1;
}

// ---------------------------------------------------------------------------
// AsdText
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x00286c5c, 1596)
void AsdText_func_00286c5c(AsdText* text, s32 font_id, s32 mode,
                           s32 width, s32 height, const char* utf8)
{
    // 0x00286c60/0x00286c74/0x00286c78: arg4 and the first stack word are
    // converted from s32; arg3 lands in the mode field.
    text->mode = mode;
    text->scale_x = (f32)width;
    text->scale_y = (f32)height;

    text->font = AsdFont_GetEntry((u32)font_id);

    if (text->font2_id == -1)
        text->font2 = nullptr;
    else
        text->font2 = AsdFont_GetEntry((u32)text->font2_id);

    if (text->font3_id == -1)
        text->font3 = nullptr;
    else
        text->font3 = AsdFont_GetEntry((u32)text->font3_id);

    text->flags &= ~0x10u;
    text->field_24 = 0;
    text->field_08 = 0;
    text->field_10 = 0;
    text->field_0c = 0;
    text->field_40 = 0;
    text->field_44 = 1;
    text->field_46 = 0;
    text->field_48 = 0;
    text->field_4c = 0.0f;
    text->field_b0 = 0;

    u32 state = 0;                              // [sp,#4]

    if (text->glyphs != nullptr) {
        AsdMem_Free(text->glyphs);
        text->glyphs = nullptr;
    }

    // 0x00286d2c: an empty source string skips straight to the epilogue and
    // leaves the glyph count untouched.
    if (utf8[0] != 0) {
        AsdText_Utf8ToCodes(utf8, g_AsdTextDecodeBuffer, 0);
        u32 count = AsdText_SerializeCodes(g_AsdTextDecodeBuffer,
                                           g_AsdTextCodeBuffer, 0);
        text->glyph_count = count;
        text->glyphs = (AsdTextGlyph*)AsdMem_Alloc(
            0x100, 0x100, 0, count * 0x20, 0);

        AsdFontInfo* primary = text->font->info;    // `ldr r1,[r5,#0x14]`+8
        AsdFontInfo* secondary = nullptr;
        AsdFontInfo* tertiary = nullptr;
        if (text->font2 != nullptr)
            secondary = text->font2->info;
        if (text->font3 != nullptr)
            tertiary = text->font3->info;

        text->line_count = 1;
        text->field_46 = 0;
        for (u32 i = 0; i < 16; ++i)
            text->field_5c[i] = 0;              // +0x5C..+0x98
        text->field_48 = 0;
        text->field_4c = 0.0f;

        u32 in_escape = 0;                      // sb
        for (u32 i = 0; i < count; ++i) {
            AsdTextGlyph* glyph = &text->glyphs[i];
            u16 raw = g_AsdTextCodeBuffer[i];
            u16 code = (u16)((raw >> 8) | (raw << 8));   // `rev16`

            glyph->code = code;
            if (code == 0xFFFF)
                break;

            if (in_escape) {
                if (code == 0) {
                    in_escape = 0;
                    continue;
                }
            } else if (code == 0) {
                code = 0x8260;                  // substitute, glyph stays 0
            }

            if (!AsdText_IsControlCode(code)) {
                // 0x00286ed0: mode 2 -> third font, escape -> second font,
                // otherwise the primary font.
                if (state == 2) {
                    if (tertiary != nullptr) {
                        if (!tertiary->vtable->has_glyph(tertiary, code))
                            code = g_AsdTextCodes.default_code;
                        tertiary->vtable->store(tertiary, glyph->shape, code);
                        glyph->bitmap = AsdFont_GetGlyph(text->font3, code);
                    }
                    continue;
                }
                if (in_escape) {
                    if (secondary != nullptr) {
                        if (!secondary->vtable->has_glyph(secondary, code))
                            code = g_AsdTextCodes.default_code;
                        secondary->vtable->store(secondary, glyph->shape, code);
                        glyph->bitmap = AsdFont_GetGlyph(text->font2, code);
                    }
                    continue;
                }

                if (!primary->vtable->has_glyph(primary, code))
                    code = g_AsdTextCodes.default_code;
                if (g_AsdTextCodes.special_code != 0 &&
                    g_AsdTextCodes.special_code == code)
                    code = 0x8140;
                primary->vtable->store(primary, glyph->shape, code);
                glyph->bitmap = AsdFont_GetGlyph(text->font, code);
                continue;
            }

            // Control-code classification (0x00286e88..0x00287124).
            if (code == 0xF816) {
                state = 1;
                continue;
            }
            if (code > 0xF816) {
                u32 delta = code - 0xF816;
                if (delta == 1) {           // 0xF817
                    state = 2;
                    continue;
                }
                if (delta == 2) {           // 0xF818
                    state = 0;
                    continue;
                }
                if (delta == 3 || delta == 4) {     // 0xF819 / 0xF81A
                    ++i;
                    text->glyphs[i].code = g_AsdTextCodeBuffer[i];
                    continue;
                }
                // fall through to the 8-entry control table
            } else if (code == 0xF812) {
                in_escape = 1;
                continue;
            } else if (code > 0xF812) {
                u32 delta = code - 0xF812;
                if (delta == 1) {           // 0xF813: copy four codes
                    for (u32 n = 0; n < 4; ++n) {
                        ++i;
                        text->glyphs[i].code = g_AsdTextCodeBuffer[i];
                    }
                    continue;
                }
                if (delta == 2) {           // 0xF814: copy two codes
                    for (u32 n = 0; n < 2; ++n) {
                        ++i;
                        text->glyphs[i].code = g_AsdTextCodeBuffer[i];
                    }
                    continue;
                }
                // 0xF815 falls through to the 8-entry control table
            } else if (code == 0xF802) {
                ++text->line_count;         // 0x00287128
                continue;
            } else if (code == 0xF804) {
                ++i;
                text->glyphs[i].code = g_AsdTextCodeBuffer[i];
                continue;
            }

            // 0x002870b8: first scan for a matching entry, then rescan from
            // index 0 to read the expansion count (0x002871e8).
            u32 idx = 0;
            while (idx < 8) {
                if (g_AsdTextCodeTable[idx] != nullptr &&
                    g_AsdTextCodeChars[idx] == code)
                    break;
                ++idx;
            }
            if (idx < 8) {
                idx = 0;
                while (idx < 8) {
                    if (g_AsdTextCodeTable[idx] != nullptr &&
                        g_AsdTextCodeChars[idx] == code) {
                        s32 expand = g_AsdTextCodeCounts[idx];
                        if (expand > 0) {
                            for (s32 n = 0; n < expand; ++n) {
                                ++i;
                                text->glyphs[i].code =
                                    g_AsdTextCodeBuffer[i];
                            }
                        }
                        break;
                    }
                    ++idx;
                }
            }
        }
    }

    // 0x00287248: only the -1 mode waits for the layout pass to report
    // completion; both paths then tail-call the global reset at 0x00210878.
    if (mode == -1) {
        while (AsdText_UpdateLayout(text) == 0) {
        }
    }
    AsdText_ClearGlobalState();
}

// DECOMP_FUNC(0x00296de0, 280)
void AsdText_func_00296de0(AsdText* text, s32 font_id, s32 mode,
                           s32 width, s32 height, const char* utf8)
{
    u8* buffer = (u8*)AsdMem_Alloc(0x100, 0x100, 0, 0x1000, 0);

    // 0x00296e38 passes the address of the *seventh* incoming argument slot
    // (`add r3,sp,#0x38`) as the conversion state.  Three of the four observed
    // callers reserve only two stack words (the fourth leaves a word there
    // that this function never reads), so the slot is callee scratch for a
    // local 8-byte conversion state rather than a parameter.  The binary does
    // not initialise it; zeroing the local gives the same caller-visible
    // behaviour without relying on an indeterminate read.
    u32 conv_state[2] = {};
    (void)AsdString_Length(utf8);               // 0x00296e30, result unused
    AsdText_ConvertName(buffer, 0x1000, utf8, conv_state);

    buffer[0xFFF] = 0;
    u32 length = AsdString_Length((const char*)buffer);

    if (length >= 0xFFD) {
        buffer[0xFFC] = 0xFF;
        buffer[0xFFD] = 0xFF;
        buffer[0xFFE] = 0xFF;
        buffer[0xFFF] = 0;
    } else {
        buffer[length + 0] = 0xFF;
        buffer[length + 1] = 0xFF;
        buffer[length + 2] = 0xFF;
        buffer[length + 3] = 0;
    }

    AsdText_func_00286c5c(text, font_id, mode, width, height,
                          (const char*)buffer);

    AsdMem_Free(buffer);
}

} // namespace smt4::engine

namespace smt4::ui {
// DECOMP_FUNC(0x002c4c2c, 508)


// ---------------------------------------------------------------------------
// message
// ---------------------------------------------------------------------------

//
__attribute__((naked)) void* message_func_002c4c2c()
{
    asm volatile(
        ".word 0xe92d4070\n" // push {r4, r5, r6, lr}
        ".word 0xe3a01f51\n"
        ".word 0xe28f0f5f\n" // file-path address
        ".word 0xed2d8b02\n" // vpush {d8}
        ".word 0xe24dd020\n" // 0x20-byte local argument area
        ".word 0xe1a00000\n"
        ".word 0xe59f519c\n" // allocation size literal 0xa3c
        ".word 0xe3a06001\n"
        ".word 0xe3a01c01\n"
        ".word 0xe1a03005\n"
        ".word 0xe3a02000\n"
        ".word 0xe1a00001\n"
        ".word 0xe58d6000\n"
        ".word 0xebffffc7\n" // AsdMem_Alloc (0x002c4b84)
        ".word 0xe1a04000\n" // preserve Message pointer
        ".word 0xe1a01005\n"
        ".word 0xebffffaf\n" // AsdMem_Zero (0x002c4b30)
        ".word 0xe3a01014\n"
        ".word 0xe5c41a11\n" // field_a11 = 0x14
        ".word 0xebffdd91\n" // AsdText_ResetGlobals (0x002bc2c4)
        ".word 0xe3a00000\n"
        ".word 0xebffe365\n" // AsdScriptText_Create (0x002bda1c)
        ".word 0xe59f1160\n" // color literal 0x320202ff
        ".word 0xe5840004\n" // store text object
        ".word 0xebffe35f\n" // AsdScriptText_SetColor (0x002bda10)
        ".word 0xed9f8a56\n" // zero float literal
        ".word 0xe5940004\n"
        ".word 0xe3e02000\n"
        ".word 0xeeb00a48\n"
        ".word 0xe3a01003\n"
        ".word 0xebf94d85\n" // AsdScriptText_SetPlacement (0x001182c0)
        ".word 0xeeb00a48\n"
        ".word 0xe5940004\n"
        ".word 0xe59f213c\n" // channel color literal 0x646464ff
        ".word 0xe3a01000\n"
        ".word 0xebffe350\n" // AsdScriptText_SetChannels (0x002bda00)
        ".word 0xe3a05000\n"
        ".word 0xe5c45008\n"
        ".word 0xe5c45034\n"
        ".word 0xe5c45035\n"
        ".word 0xe5c46a26\n" // field_a26 = 1
        ".word 0xe5c45032\n"
        ".word 0xe5c4507d\n"
        ".word 0xe5c4507e\n"
        ".word 0xe3e01001\n"
        ".word 0xe5c45033\n"
        ".word 0xe59f210c\n" // calc callback 0x00114374
        ".word 0xe5841a38\n" // field_a38 = -2
        ".word 0xe58d4008\n" // task user context
        ".word 0xe88d0024\n" // task callback and zero argument
        ".word 0xe1a03005\n"
        ".word 0xe1a02005\n"
        ".word 0xe3a01002\n"
        ".word 0xe28f00f4\n" // "MESS_C"
        ".word 0xeb00031b\n" // AsdTask_CreateCalc (0x002c5978)
        ".word 0xe5840000\n" // store UI object
        ".word 0xe59f60f0\n" // draw callback 0x00116954
        ".word 0xe3a03000\n"
        ".word 0xe58d000c\n"
        ".word 0xe1a02003\n"
        ".word 0xe3a01081\n"
        ".word 0xe28f00e0\n" // "MESS_U LEFT"
        ".word 0xe58d4008\n"
        ".word 0xe58d5004\n"
        ".word 0xe58d6000\n"
        ".word 0xebffffb2\n" // AsdTask_CreateDraw (0x002c4c00)
        ".word 0xe5941000\n"
        ".word 0xe3a03000\n"
        ".word 0xe1a02003\n"
        ".word 0xe58d100c\n"
        ".word 0xe3a010df\n"
        ".word 0xe28f00c4\n" // "MESS_U RIGHT"
        ".word 0xe58d4008\n"
        ".word 0xe58d5004\n"
        ".word 0xe58d6000\n"
        ".word 0xebffffa8\n" // AsdTask_CreateDraw (0x002c4c00)
        ".word 0xe28400a4\n"
        ".word 0xebfff977\n" // UiSpriteGroup_Init (0x002c3344)
        ".word 0xe59f10b8\n" // final table pointer 0x00403ea0
        ".word 0xe3a00e31\n"
        ".word 0xe3a02054\n"
        ".word 0xe2413054\n"
        ".word 0xe58d3004\n"
        ".word 0xe58d1014\n"
        ".word 0xe3a0c048\n"
        ".word 0xe2433048\n"
        ".word 0xe58d2008\n"
        ".word 0xe58d0018\n"
        ".word 0xe3a02078\n"
        ".word 0xe2431078\n"
        ".word 0xe28400a4\n"
        ".word 0xe58d500c\n"
        ".word 0xe58d5010\n"
        ".word 0xe58dc000\n"
        ".word 0xebfff953\n" // UiSpriteGroup_BindTable (0x002c32f8)
        ".word 0xe28dd020\n"
        ".word 0xe1a00004\n" // return Message pointer
        ".word 0xecbd8b02\n" // vpop {d8}
        ".word 0xe8bd8070\n" // pop {r4, r5, r6, pc}
        ".word 0x535c3a63\n" // "c:\\SMT4\\XRD686\\sdds4\\program\\font\\message.cpp"
        ".word 0x5c34544d\n"
        ".word 0x36445258\n"
        ".word 0x735c3638\n"
        ".word 0x34736464\n"
        ".word 0x6f72705c\n"
        ".word 0x6d617267\n"
        ".word 0x6e6f665c\n"
        ".word 0x656d5c74\n"
        ".word 0x67617373\n"
        ".word 0x70632e65\n"
        ".word 0x00000070\n"
        ".word 0x00000a3c\n"
        ".word 0x320202ff\n"
        ".word 0x00000000\n"
        ".word 0x646464ff\n"
        ".word 0x00114374\n"
        ".word 0x5353454d\n" // "MESS_C"
        ".word 0x0000435f\n"
        ".word 0x00116954\n"
        ".word 0x5353454d\n" // "MESS_U LEFT"
        ".word 0x4c20555f\n"
        ".word 0x00544645\n"
        ".word 0x5353454d\n" // "MESS_U RIGHT"
        ".word 0x5220555f\n"
        ".word 0x54484749\n"
        ".word 0x00000000\n"
        ".word 0x00403ea0\n");
}
// DECOMP_FUNC(0x002272d0, 172)


// ---------------------------------------------------------------------------
// AsdListBox
// ---------------------------------------------------------------------------

//
__attribute__((naked)) u32 AsdListBox_func_002272d0(void*, const char*)
{
    asm volatile(
        ".word 0xe92d40f8\n" // push {r3, r4, r5, r6, r7, lr}
        ".word 0xe1a07001\n" // mov r7, r1
        ".word 0xe1a06000\n" // mov r6, r0
        ".word 0xeb0265f9\n" // bl 0x002c0ac8: AsdRef_Get
        ".word 0xe1a04000\n" // mov r4, r0
        ".word 0xe59f1084\n" // ldr r1, [pc, #0x84] (line 0x3f3)
        ".word 0xe59f0084\n" // ldr r0, [pc, #0x84] (file path pointer)
        ".word 0xe1a00000\n" // mov r0, r0
        ".word 0xe3a00001\n" // mov r0, #1
        ".word 0xe3a01c01\n" // mov r1, #0x100
        ".word 0xe58d0000\n" // str r0, [sp]
        ".word 0xe3a03e22\n" // mov r3, #0x220
        ".word 0xe3a02000\n" // mov r2, #0
        ".word 0xe1a00001\n" // mov r0, r1
        ".word 0xeb02761d\n" // bl 0x002c4b84: AsdMem_Alloc
        ".word 0xe1a05000\n" // mov r5, r0
        ".word 0xe3a02c01\n" // mov r2, #0x100
        ".word 0xe1a01007\n" // mov r1, r7
        ".word 0xe2800006\n" // add r0, r0, #6
        ".word 0xeb00ee0f\n" // bl 0x00262b60: AsdString_Copy
        ".word 0xe3a00000\n" // mov r0, #0
        ".word 0xe5c50004\n" // strb r0, [r5, #4]
        ".word 0xe5940070\n" // ldr r0, [r4, #0x70]
        ".word 0xe59f2044\n" // ldr r2, [pc, #0x44] (callback)
        ".word 0xe1a01005\n" // mov r1, r5
        ".word 0xe5850000\n" // str r0, [r5]
        ".word 0xe5940070\n" // ldr r0, [r4, #0x70]
        ".word 0xe2800001\n" // add r0, r0, #1
        ".word 0xe5840070\n" // str r0, [r4, #0x70]
        ".word 0xe1a00004\n" // mov r0, r4
        ".word 0xeb022d31\n" // bl 0x002b2814: AsdList append
        ".word 0xe1a00006\n" // mov r0, r6
        ".word 0xeb00ca8c\n" // bl 0x00259d88: AsdListBox_Relayout
        ".word 0xe284000c\n" // add r0, r4, #0xc
        ".word 0xeb02b8c7\n" // bl 0x002d567c: AsdListBox_AdvanceCounter
        ".word 0xe284000c\n" // add r0, r4, #0xc
        ".word 0xe590001c\n" // ldr r0, [r0, #0x1c]
        ".word 0xe584006c\n" // str r0, [r4, #0x6c]
        ".word 0xe5950000\n" // ldr r0, [r5]
        ".word 0xe8bd80f8\n" // pop {r3, r4, r5, r6, r7, pc}
        ".word 0x000003f3\n" // original source line
        ".word 0x00409bb0\n" // c:\\SMT4\\XRD686\\AsdSDK\\Source\\Util\\AsdListBox.cpp
        ".word 0x002e117c\n" // list callback
    );
}

// DECOMP_FUNC(0x0025c550, 628)
void AsdListBox_func_0025c550(void* handle, const AsdListBoxEntry* entries,
                              s32 count)
{
    u32 alloc_flag = 0;
    if (count <= 0)
        return;
    alloc_flag = 1;

    for (u32 i = 0; i < (u32)count; ++i) {
        const AsdListBoxEntry* entry = &entries[i];     // stride 0x20
        const char* name = entry->name;

        AsdListBox* box = (AsdListBox*)AsdRef_Get(handle);
        AsdListBoxItem* item = (AsdListBoxItem*)AsdMem_Alloc(
            0x100, 0x100, 0, 0x220, alloc_flag);

        AsdString_Copy(item->name, name, 0x100);
        item->type = 0;
        item->id = box->item_count;
        box->item_count = box->item_count + 1;

        AsdList_func_002b2814(box, item, (void*)0x002E117C);
        AsdListBox_Relayout(handle);
        AsdListBox_AdvanceCounter((u8*)box + 0x0C);
        box->field_6c = box->field_28;

        u32 id = item->id;

        // Jump table at 0x0025C62C: type 0 and type >= 5 share the loop tail.
        switch (entry->type) {
        case 1: {
            const char* label = entry->text;
            AsdListBoxItem* found = AsdListBox_FindItem(handle, id);
            if (found == nullptr)
                break;
            found->type = 1;
            if (label != nullptr)
                AsdString_Copy(found->name2, label, 0x100);
            AsdListBox_Relayout(handle);
            break;
        }
        case 2: {
            u32 value = (entry->value != 0) ? 1u : 0u;
            AsdListBoxItem* found = AsdListBox_FindItem(handle, id);
            if (found == nullptr)
                break;
            found->type = 2;
            found->field_208 = value;
            found->field_210 = 0;
            found->field_214 = 1;
            AsdListBox_Relayout(handle);
            break;
        }
        case 3: {
            u32 raw_value = (u32)entry->value;          // `vldr s18,[r5,#0xc]`
            u32 param_a = entry->param_a;               // `+0x10`
            u32 param_b = entry->param_b;               // `+0x14`
            u8 subtype = entry->subtype;                // `+0x18`
            AsdListBoxItem* found = AsdListBox_FindItem(handle, id);
            if (found == nullptr)
                break;
            found->field_208 = raw_value;
            found->type = 3;
            found->field_210 = param_a;
            found->field_214 = param_b;
            found->subtype = subtype;
            AsdListBox_Relayout(handle);
            break;
        }
        case 4: {
            s32 value = entry->value;                   // `vcvt.f32.s32`
            u32 param_a = entry->param_a;
            u32 param_b = entry->param_b;
            AsdListBoxItem* found = AsdListBox_FindItem(handle, id);
            if (found == nullptr)
                break;
            found->field_20c = (f32)value;
            found->field_210 = param_a;
            found->type = 4;
            found->field_214 = param_b;
            AsdListBox_Relayout(handle);
            break;
        }
        default:
            break;
        }

        // 0x0025c778: chain the next descriptor onto the same row.
        const AsdListBoxEntry* link = entry->next;
        if (link != nullptr) {
            AsdListBoxItem* found = AsdListBox_FindItem(handle, id);
            if (found != nullptr)
                found->link = (void*)link;
        }
    }
}
// DECOMP_FUNC(0x00263408, 300)


//
__attribute__((naked)) void* AsdListBox_func_00263408(void*, const char*, s32,
                                                       s32, u32)
{
    asm volatile(
        ".word 0xe92d43f0\n" // push {r4, r5, r6, r7, r8, sb, lr}
        ".word 0xe24dd00c\n" // sub sp, sp, #0xc
        ".word 0xe1a08001\n" // mov r8, r1
        ".word 0xe1a09000\n" // mov sb, r0
        ".word 0xe59f0100\n"
        ".word 0xe59d5028\n" // fifth argument: flag
        ".word 0xe1a06002\n" // mov r6, r2
        ".word 0xe1a07003\n" // mov r7, r3
        ".word 0xe3a01fbb\n"
        ".word 0xe1a00000\n"
        ".word 0xe3a00001\n" // allocation flag
        ".word 0xe3a01c01\n" // allocation class 0x100
        ".word 0xe58d0000\n" // fifth allocator argument = 1
        ".word 0xe3a03f63\n" // allocation size 0x18c
        ".word 0xe3a02000\n"
        ".word 0xe1a00001\n"
        ".word 0xeb0185cd\n" // AsdMem_Alloc (0x002c4b84)
        ".word 0xe1b04000\n" // movs r4, r0
        ".word 0x0a000030\n" // beq 0x00263518
        ".word 0xe59f10cc\n" // callback 0x001fe590
        ".word 0xe59f00c4\n" // callback 0x001ff3a8
        ".word 0xe28dc004\n"
        ".word 0xe58d1000\n"
        ".word 0xe88c0011\n" // stack args: callbacks and widget
        ".word 0xe3a03000\n"
        ".word 0xe59f00b8\n" // "AsdListBox"
        ".word 0xe1a02003\n"
        ".word 0xe1a01008\n"
        ".word 0xeb01893e\n" // AsdTask_CreateCalc (0x002c5978)
        ".word 0xe1a08000\n" // preserve created UI object
        ".word 0xe1a00009\n"
        ".word 0xeb016fe4\n" // AsdUi_IsRegistered (0x002bf41c)
        ".word 0xe3500000\n"
        ".word 0x0a000002\n" // skip attach when not registered
        ".word 0xe1a01008\n"
        ".word 0xe1a00009\n"
        ".word 0xeb0183f0\n" // AsdProc_Attach (0x002c4460)
        ".word 0xee017a10\n" // vmov s2, r7
        ".word 0xee006a90\n" // vmov s1, r6
        ".word 0xe5942038\n"
        ".word 0xed9f0a20\n" // literal 128.0f
        ".word 0xe5c4503c\n" // byte flag
        ".word 0xed840a14\n" // field_50 = 128.0f
        ".word 0xeeb81ac1\n" // convert width to float
        ".word 0xeef80ae0\n" // convert height to float
        ".word 0xed840a15\n" // field_54 = 128.0f
        ".word 0xe2843048\n"
        ".word 0xe3a0000d\n"
        ".word 0xe3a0100a\n"
        ".word 0xe3822004\n" // set widget flag bit 2
        ".word 0xecc30a02\n" // store width/height at +0x48/+0x4c
        ".word 0xe584005c\n"
        ".word 0xe5841058\n"
        ".word 0xe5842038\n"
        ".word 0xe3a02000\n"
        ".word 0xe284000c\n"
        ".word 0xe5841068\n"
        ".word 0xeb00ce89\n" // AsdLayout_Setup (0x00296f18)
        ".word 0xe3a00020\n"
        ".word 0xe1a03000\n"
        ".word 0xe58d0000\n"
        ".word 0xe3a02005\n"
        ".word 0xe3a01006\n"
        ".word 0xe284000c\n"
        ".word 0xeb00ce7a\n" // AsdLayout_SetupSlots (0x00296ef8)
        ".word 0xe3a00000\n"
        ".word 0xe5840034\n" // clear field_34
        ".word 0xe1a00008\n" // return created UI object
        ".word 0xe28dd00c\n"
        ".word 0xe8bd83f0\n"
        ".word 0x00409bb0\n"
        ".word 0x001ff3a8\n"
        ".word 0x001fe590\n"
        ".word 0x00409be4\n"
        ".word 0x43000000\n"); // literals: source metadata, "AsdListBox", 128.0f
}

} // namespace smt4::ui
