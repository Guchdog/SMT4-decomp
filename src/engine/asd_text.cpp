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
    // 0x002c5978.  r0 is the widget kind/label; r1 carries the row name in
    // AsdListBox_func_00263408 and the numeric id 2 in message_func_002c4c2c,
    // hence the pointer-sized integer slot.
    void* AsdUi_Create(const char* kind, std::uintptr_t name, u32 a2, u32 a3,
                       u32 cb0, u32 cb1, void* obj);                        // 0x002c5978
    void* AsdUi_CreateLabel(const char* name, u32 id, u32 a1, u32 a2,
                            u32 p0, u32 p1, void* p2, u32 p3);               // 0x002c4c00
    int   AsdUi_IsRegistered(void* handle);                                 // 0x002bf41c
    void  AsdUi_Attach(void* handle, void* object);                         // 0x002c4460
    void  AsdText_ResetGlobals();                                           // 0x002bc2c4
    void  AsdScriptText_SetChannels(void* obj, u32 a1, u32 a2, f32 value);  // 0x002bda00
    void  AsdScriptText_SetColor(void* obj, u32 color);                     // 0x002bda10
    void* AsdScriptText_Create(u32 index);                                  // 0x002bda1c
    void  AsdScriptText_SetPlacement(void* obj, u32 a1, u32 a2, f32 value); // 0x001182c0
    void  AsdLayout_Zero(void* block);                                      // 0x002c3344
    void  AsdLayout_Init(smt4::ui::AsdLayoutRect* rect, u32 a1, u32 a2,
                         u32 a3, u32 a4, u32 a5, u32 a6, u32 a7, u32 a8,
                         u32 a9, u32 a10);                                  // 0x002c32f8
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

// ---------------------------------------------------------------------------
// AsdFont
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x0010a588, 152)
void AsdFont_func_0010a588(s32 count)
{
    // Debug string "SJIS" + line 0x269 are passed before the table is sized;
    // the allocator arguments below are the live ones (r1 is reloaded to
    // 0x100 at 0x0010a5bc).
    Crt_SetEncoding(2, "SJIS");

    g_AsdFontManager.count = (u32)count;
    g_AsdFontManager.entries = (AsdFontEntry*)AsdMem_AllocAlign(
        0x100, 0x100, 0, (u32)count * 0x2C, 1);
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

// ---------------------------------------------------------------------------
// message
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x002c4c2c, 508)
void* message_func_002c4c2c()
{
    Message* msg = (Message*)AsdMem_Alloc(0x100, 0x100, 0, 0xA3C, 1);
    AsdMem_Zero(msg, 0xA3C);

    msg->field_a11 = 0x14;
    AsdText_ResetGlobals();                     // 0x002bc2c4
    msg->text = AsdScriptText_Create(0);        // 0x002bda1c
    AsdScriptText_SetColor(msg->text, 0x320202FF);
    AsdScriptText_SetPlacement(msg->text, 3, 0xFFFFFFFF, 0.0f);
    AsdScriptText_SetChannels(msg->text, 0, 0x646464FF, 0.0f);

    msg->field_08 = 0;
    msg->field_34 = 0;
    msg->field_35 = 0;
    msg->field_a26 = 1;
    msg->field_32 = 0;
    msg->field_7d = 0;
    msg->field_7e = 0;
    msg->field_33 = 0;
    msg->field_a38 = -2;

    msg->ui = AsdUi_Create("MESS_C", 2, 0, 0, 0x00114374, 0, msg);

    AsdUi_CreateLabel("MESS_U LEFT", 0x81, 0, 0, 0x00116954, 0, msg,
                      (u32)(std::uintptr_t)msg->ui);

    AsdUi_CreateLabel("MESS_U RIGHT", 0xDF, 0, 0, 0x00116954, 0, msg,
                      (u32)(std::uintptr_t)msg->ui);

    AsdLayout_Zero(&msg->layout);
    AsdLayout_Init(&msg->layout,
                   0x00403D8C, 0x78, 0x00403E04, 0x48,
                   0x00403E4C, 0x54, 0, 0,
                   0x00403EA0, 0x310);

    return msg;
}

// ---------------------------------------------------------------------------
// AsdListBox
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x002272d0, 172)
u32 AsdListBox_func_002272d0(void* handle, const char* name)
{
    AsdListBox* box = (AsdListBox*)AsdRef_Get(handle);
    AsdListBoxItem* item = (AsdListBoxItem*)AsdMem_Alloc(
        0x100, 0x100, 0, 0x220, 1);

    AsdString_Copy(item->name, name, 0x100);
    item->type = 0;

    item->id = box->item_count;
    box->item_count = box->item_count + 1;

    AsdList_func_002b2814(box, item, (void*)0x002E117C);
    AsdListBox_Relayout(handle);
    AsdListBox_AdvanceCounter((u8*)box + 0x0C);
    box->field_6c = box->field_28;

    return item->id;
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
void* AsdListBox_func_00263408(void* handle, const char* name, s32 width,
                               s32 height, u32 flag)
{
    AsdListBoxWidget* widget = (AsdListBoxWidget*)AsdMem_Alloc(
        0x100, 0x100, 0, 0x18C, 1);
    if (widget == nullptr)
        return nullptr;

    void* created = AsdUi_Create("AsdListBox", (std::uintptr_t)name,
                                 0, 0, 0x001FE590, 0x001FF3A8, widget);

    if (AsdUi_IsRegistered(handle) != 0)
        AsdUi_Attach(handle, created);

    widget->field_38 = widget->field_38 | 4;
    widget->field_3c = (u8)flag;
    widget->field_48 = (f32)width;
    widget->field_4c = (f32)height;
    widget->field_50 = 128.0f;
    widget->field_54 = 128.0f;
    widget->field_58 = 0x0A;
    widget->field_5c = 0x0D;
    widget->field_68 = 0x0A;

    AsdLayout_Setup((u8*)widget + 0x0C, 0x0A, 0);
    AsdLayout_SetupSlots((u8*)widget + 0x0C, 6, 5, 0x20, 0x20);

    widget->field_34 = 0;

    return created;
}

} // namespace smt4::ui
