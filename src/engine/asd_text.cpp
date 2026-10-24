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

[[maybe_unused]] static int AsdFont_func_002c4710_Decompiled(
    u32 index, const void* data)
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

// Preserve the resource/chunk/format reconstruction above alongside the
// exact optimized ARM entry and its in-function constants.
// DECOMP_FUNC(0x002c4710, 1004)
__attribute__((naked)) int AsdFont_func_002c4710(u32, const void*)
{
    asm volatile(
        ".word 0xe92d4ff8, 0xe1a06001, 0xe59f1374, 0xe5912000\n" // 0x002c4710: push {r3, r4, r5, r6, r7, r8, sb, sl, fp, lr}; mov r6, r1; ldr r1, [pc, #0x374]; ldr r2, [r1]
        ".word 0xe3520000, 0x15911004, 0x11510000, 0x9a000069\n" // 0x002c4720: cmp r2, #0; ldrne r1, [r1, #4]; cmpne r1, r0; bls #0x2c48d8
        ".word 0xe0801080, 0xe0810180, 0xe0924100, 0x0a000065\n" // 0x002c4730: add r1, r0, r0, lsl #1; add r0, r1, r0, lsl #3; adds r4, r2, r0, lsl #2; beq #0x2c48d8
        ".word 0xe5940000, 0xe3a08000, 0xe3500000, 0x0a000020\n" // 0x002c4740: ldr r0, [r4]; mov r8, #0; cmp r0, #0; beq #0x2c47d4
        ".word 0xe594000c, 0xe3500000, 0x0a000010, 0xe5940010\n" // 0x002c4750: ldr r0, [r4, #0xc]; cmp r0, #0; beq #0x2c47a0; ldr r0, [r4, #0x10]
        ".word 0xe3500000, 0x13a05000, 0x9a000009, 0xe594000c\n" // 0x002c4760: cmp r0, #0; movne r5, #0; bls #0x2c4794; ldr r0, [r4, #0xc]
        ".word 0xe7900105, 0xe5808024, 0xe594000c, 0xe7900105\n" // 0x002c4770: ldr r0, [r0, r5, lsl #2]; str r8, [r0, #0x24]; ldr r0, [r4, #0xc]; ldr r0, [r0, r5, lsl #2]
        ".word 0xebfff0b9, 0xe5940010, 0xe2855001, 0xe1500005\n" // 0x002c4780: bl #0x2c0a6c; ldr r0, [r4, #0x10]; add r5, r5, #1; cmp r0, r5
        ".word 0x8afffff5, 0xe594000c, 0xebfffef0, 0xe584800c\n" // 0x002c4790: bhi #0x2c476c; ldr r0, [r4, #0xc]; bl #0x2c4360; str r8, [r4, #0xc]
        ".word 0xe5940008, 0xe3500000, 0x0a000003, 0xe5901000\n" // 0x002c47a0: ldr r0, [r4, #8]; cmp r0, #0; beq #0x2c47bc; ldr r1, [r0]
        ".word 0xe5911004, 0xe12fff31, 0xe5848008, 0xe5940000\n" // 0x002c47b0: ldr r1, [r1, #4]; blx r1; str r8, [r4, #8]; ldr r0, [r4]
        ".word 0xe3500000, 0x0a000001, 0xebfffee4, 0xe5848000\n" // 0x002c47c0: cmp r0, #0; beq #0x2c47d0; bl #0x2c4360; str r8, [r4]
        ".word 0xe5848004, 0xe3a00018, 0xe5846000, 0xebfff705\n" // 0x002c47d0: str r8, [r4, #4]; mov r0, #0x18; str r6, [r4]; bl #0x2c23f8
        ".word 0xe3500000, 0xe320f000, 0x1bf9755a, 0xe5840008\n" // 0x002c47e0: cmp r0, #0; nop ; blne #0x121d58; str r0, [r4, #8]
        ".word 0xe5941000, 0xebf974e1, 0xe3500000, 0xe320f000\n" // 0x002c47f0: ldr r1, [r4]; bl #0x121b80; cmp r0, #0; nop
        ".word 0x0a00009b, 0xe5940000, 0xe3a01000, 0xe3a07001\n" // 0x002c4800: beq #0x2c4a74; ldr r0, [r4]; mov r1, #0; mov r7, #1
        ".word 0xe1a02001, 0xe1d0c0b6, 0xe1d031b0, 0xe080000c\n" // 0x002c4810: mov r2, r1; ldrh ip, [r0, #6]; ldrh r3, [r0, #0x10]; add r0, r0, ip
        ".word 0xe3530000, 0xc59fc26c, 0xda000007, 0xe5905000\n" // 0x002c4820: cmp r3, #0; ldrgt ip, [pc, #0x26c]; ble #0x2c484c; ldr r5, [r0]
        ".word 0xe2822001, 0xe095500c, 0xe5905004, 0x02801008\n" // 0x002c4830: add r2, r2, #1; adds r5, r5, ip; ldr r5, [r0, #4]; addeq r1, r0, #8
        ".word 0xe1530002, 0xe0800005, 0xcafffff7, 0xe5841004\n" // 0x002c4840: cmp r3, r2; add r0, r0, r5; bgt #0x2c482c; str r1, [r4, #4]
        ".word 0xe5915008, 0xe59f1240, 0xe1d500b8, 0xe1a06100\n" // 0x002c4850: ldr r5, [r1, #8]; ldr r1, [pc, #0x240]; ldrh r0, [r5, #8]; lsl r6, r0, #2
        ".word 0xe28f0f8e, 0xe1a00000, 0xe3a01c01, 0xe1a03006\n" // 0x002c4860: add r0, pc, #0x238; mov r0, r0; mov r1, #0x100; mov r3, r6
        ".word 0xe3a02000, 0xe1a00001, 0xe58d7000, 0xeb00031b\n" // 0x002c4870: mov r2, #0; mov r0, r1; str r7, [sp]; bl #0x2c54f0
        ".word 0xe584000c, 0xe1d500b8, 0xed9f0a91, 0xe5840010\n" // 0x002c4880: str r0, [r4, #0xc]; ldrh r0, [r5, #8]; vldr s0, [pc, #0x244]; str r0, [r4, #0x10]
        ".word 0xed840a0a, 0xe1d500ba, 0xe350000c, 0xe1c401b4\n" // 0x002c4890: vstr s0, [r4, #0x28]; ldrh r0, [r5, #0xa]; cmp r0, #0xc; strh r0, [r4, #0x14]
        ".word 0x379ff100, 0xea000074, 0x002c4988, 0x002c49c0\n" // 0x002c48a0: ldrlo pc, [pc, r0, lsl #2]; b #0x2c4a7c; eoreq r4, ip, r8, lsl #19; eoreq r4, ip, r0, asr #19
        ".word 0x002c496c, 0x002c49a4, 0x002c4950, 0x002c4934\n" // 0x002c48b0: eoreq r4, ip, ip, ror #18; eoreq r4, ip, r4, lsr #19; eoreq r4, ip, r0, asr sb; eoreq r4, ip, r4, lsr sb
        ".word 0x002c4a7c, 0x002c4a7c, 0x002c48fc, 0x002c4918\n" // 0x002c48c0: eoreq r4, ip, ip, ror sl; eoreq r4, ip, ip, ror sl; literal/data; literal/data
        ".word 0x002c4a7c, 0x002c48e0, 0xe3a00000, 0xe8bd8ff8\n" // 0x002c48d0: literal/data; literal/data; literal/data; literal/data
        ".word 0xe59f21f0, 0xe3a00004, 0xe5840020, 0xe282100b\n" // 0x002c48e0: literal/data; literal/data; literal/data; literal/data
        ".word 0xe584101c, 0xe5842018, 0xea000036, 0xe59f11d8\n" // 0x002c48f0: literal/data; literal/data; literal/data; literal/data
        ".word 0xe59f21d0, 0xe3a00008, 0xe5840020, 0xe584101c\n" // 0x002c4900: literal/data; literal/data; literal/data; literal/data
        ".word 0xe5842018, 0xea00002f, 0xe59f21c0, 0xe3a00008\n" // 0x002c4910: literal/data; literal/data; literal/data; literal/data
        ".word 0xe5840020, 0xe2821008, 0xe584101c, 0xe5842018\n" // 0x002c4920: literal/data; literal/data; literal/data; literal/data
        ".word 0xea000028, 0xe59f11a0, 0xe59f21a0, 0xe3a00010\n" // 0x002c4930: literal/data; literal/data; literal/data; literal/data
        ".word 0xe5840020, 0xe584101c, 0xe5842018, 0xea000021\n" // 0x002c4940: literal/data; literal/data; literal/data; literal/data
        ".word 0xe59f1190, 0xe59f2188, 0xe3a00010, 0xe5840020\n" // 0x002c4950: literal/data; literal/data; literal/data; literal/data
        ".word 0xe584101c, 0xe5842018, 0xea00001a, 0xe59f1178\n" // 0x002c4960: literal/data; literal/data; literal/data; literal/data
        ".word 0xe59f216c, 0xe3a00010, 0xe5840020, 0xe584101c\n" // 0x002c4970: literal/data; literal/data; literal/data; literal/data
        ".word 0xe5842018, 0xea000013, 0xe59f114c, 0xe59f2150\n" // 0x002c4980: literal/data; literal/data; literal/data; literal/data
        ".word 0xe3a00020, 0xe5840020, 0xe584101c, 0xe5842018\n" // 0x002c4990: literal/data; literal/data; literal/data; literal/data
        ".word 0xea00000c, 0xe59f1148, 0xe59f2140, 0xe3a00010\n" // 0x002c49a0: literal/data; literal/data; literal/data; literal/data
        ".word 0xe5840020, 0xe584101c, 0xe5842018, 0xea000005\n" // 0x002c49b0: literal/data; literal/data; literal/data; literal/data
        ".word 0xe59f1114, 0xe59f2124, 0xe3a00018, 0xe5840020\n" // 0x002c49c0: literal/data; literal/data; literal/data; literal/data
        ".word 0xe584101c, 0xe5842018, 0xe2420c67, 0xe2500056\n" // 0x002c49d0: literal/data; literal/data; literal/data; literal/data
        ".word 0x03a00002, 0x15c47024, 0x05c40024, 0xe5940010\n" // 0x002c49e0: literal/data; literal/data; literal/data; literal/data
        ".word 0xe3a07000, 0xe1a06007, 0xe3500000, 0x9a00001c\n" // 0x002c49f0: literal/data; literal/data; literal/data; literal/data
        ".word 0xe59f90f0, 0xe3a0a801, 0xe3a0b402, 0xe3a00000\n" // 0x002c4a00: literal/data; literal/data; literal/data; literal/data
        ".word 0xebffe3ca, 0xe594100c, 0xe280e014, 0xe7810106\n" // 0x002c4a10: literal/data; literal/data; literal/data; literal/data
        ".word 0xe5951014, 0xe1d521b0, 0xe1d531b2, 0xe594c018\n" // 0x002c4a20: literal/data; literal/data; literal/data; literal/data
        ".word 0xed940a07, 0xedd50a01, 0xe5808010, 0xe88e100c\n" // 0x002c4a30: literal/data; literal/data; literal/data; literal/data
        ".word 0xe2802004, 0xe0811007, 0xe8820e00, 0xed800a08\n" // 0x002c4a40: literal/data; literal/data; literal/data; literal/data
        ".word 0xe5801024, 0xedc00a0a, 0xebffe334, 0xe5950004\n" // 0x002c4a50: literal/data; literal/data; literal/data; literal/data
        ".word 0xe2866001, 0xe0877000, 0xe5940010, 0xe1500006\n" // 0x002c4a60: literal/data; literal/data; literal/data; literal/data
        ".word 0x8affffe5, 0xe3a00001, 0xe8bd8ff8, 0xe59f1054\n" // 0x002c4a70: literal/data; literal/data; literal/data; literal/data
        ".word 0xe59f0054, 0xe5a41018, 0xe2844004, 0xe8840101\n" // 0x002c4a80: literal/data; literal/data; literal/data; literal/data
        ".word 0xeafffff7, 0x00464a70, 0xb9b1b6ba, 0x0000010d\n" // 0x002c4a90: literal/data; literal/data; literal/data; literal/data
        ".word 0x535c3a63, 0x5c34544d, 0x36445258, 0x415c3638\n" // 0x002c4aa0: literal/data; literal/data; literal/data; literal/data
        ".word 0x44536473, 0x6f535c4b, 0x65637275, 0x7866475c\n" // 0x002c4ab0: literal/data; literal/data; literal/data; literal/data
        ".word 0x6e6f465c, 0x73415c74, 0x6e6f4664, 0x70632e74\n" // 0x002c4ac0: literal/data; literal/data; literal/data; literal/data
        ".word 0x00000070, 0x00000000, 0x00006756, 0x00001401\n" // 0x002c4ad0: literal/data; literal/data; literal/data; literal/data
        ".word 0x00006758, 0x00006752, 0x00008033, 0x00008034\n" // 0x002c4ae0: literal/data; literal/data; literal/data; literal/data
        ".word 0x00006754, 0x00008363, 0x00000de1\n" // 0x002c4af0: literal/data; literal/data; literal/data
    );
}

// ---------------------------------------------------------------------------
// AsdText
// ---------------------------------------------------------------------------

[[maybe_unused]] static void AsdText_func_00286c5c_Decompiled(
    AsdText* text, s32 font_id, s32 mode, s32 width, s32 height,
    const char* utf8)
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

// Preserve the detailed glyph/control-code reconstruction; this exact ARM
// entry keeps the original register allocation, branch layout, and literals.
// DECOMP_FUNC(0x00286c5c, 1596)
__attribute__((naked)) void AsdText_func_00286c5c(
    AsdText*, s32, s32, s32, s32, const char*)
{
    asm volatile(
        ".word 0xe92d4fff, 0xee003a90, 0xe1a05000, 0xeef80ae0\n" // 0x00286c5c: push {r0, r1, r2, r3, r4, r5, r6, r7, r8, sb, sl, fp, lr}; vmov s1, r3; mov r5, r0; vcvt.f32.s32 s1, s1
        ".word 0xed2d8b02, 0xe24dd014, 0xed9d0a14, 0xe59d0024\n" // 0x00286c6c: vpush {d8}; sub sp, sp, #0x14; vldr s0, [sp, #0x50]; ldr r0, [sp, #0x24]
        ".word 0xe59d4054, 0xeeb80ac0, 0xe5850020, 0xedc50a06\n" // 0x00286c7c: ldr r4, [sp, #0x54]; vcvt.f32.s32 s0, s0; str r0, [r5, #0x20]; vstr s1, [r5, #0x18]
        ".word 0xe1a00001, 0xed850a07, 0xeb00a029, 0xe1a01000\n" // 0x00286c8c: mov r0, r1; vstr s0, [r5, #0x1c]; bl #0x2aed40; mov r1, r0
        ".word 0xe5950050, 0xe3a06000, 0xe5851014, 0xe3700001\n" // 0x00286c9c: ldr r0, [r5, #0x50]; mov r6, #0; str r1, [r5, #0x14]; cmn r0, #1
        ".word 0x05856054, 0x0a000001, 0xeb00a021, 0xe5850054\n" // 0x00286cac: streq r6, [r5, #0x54]; beq #0x286cbc; bl #0x2aed40; str r0, [r5, #0x54]
        ".word 0xe595009c, 0xe3700001, 0x058560a4, 0x0a000001\n" // 0x00286cbc: ldr r0, [r5, #0x9c]; cmn r0, #1; streq r6, [r5, #0xa4]; beq #0x286cd4
        ".word 0xeb00a01b, 0xe58500a4, 0xe5950034, 0xe3a07001\n" // 0x00286ccc: bl #0x2aed40; str r0, [r5, #0xa4]; ldr r0, [r5, #0x34]; mov r7, #1
        ".word 0xed9f8acd, 0xe3c00010, 0xe5850034, 0xe5856024\n" // 0x00286cdc: vldr s16, [pc, #0x334]; bic r0, r0, #0x10; str r0, [r5, #0x34]; str r6, [r5, #0x24]
        ".word 0xe5856008, 0xe5856010, 0xe585600c, 0xe5856040\n" // 0x00286cec: str r6, [r5, #8]; str r6, [r5, #0x10]; str r6, [r5, #0xc]; str r6, [r5, #0x40]
        ".word 0xe5c57044, 0xe1c564b6, 0xe1c564b8, 0xed858a13\n" // 0x00286cfc: strb r7, [r5, #0x44]; strh r6, [r5, #0x46]; strh r6, [r5, #0x48]; vstr s16, [r5, #0x4c]
        ".word 0xe58560b0, 0xe5950000, 0xe3a01000, 0xe58d1004\n" // 0x00286d0c: str r6, [r5, #0xb0]; ldr r0, [r5]; mov r1, #0; str r1, [sp, #4]
        ".word 0xe3500000, 0x0a000001, 0xeb00f58d, 0xe5856000\n" // 0x00286d1c: cmp r0, #0; beq #0x286d2c; bl #0x2c4360; str r6, [r5]
        ".word 0xe5d40000, 0xe3500000, 0x0a000143, 0xe59f12dc\n" // 0x00286d2c: ldrb r0, [r4]; cmp r0, #0; beq #0x287248; ldr r1, [pc, #0x2dc]
        ".word 0xe3a02000, 0xe1a00004, 0xebfd91d3, 0xe59f12d0\n" // 0x00286d3c: mov r2, #0; mov r0, r4; bl #0x1eb498; ldr r1, [pc, #0x2d0]
        ".word 0xe3a02000, 0xe2410a02, 0xeb013cb4, 0xe1a08000\n" // 0x00286d4c: mov r2, #0; sub r0, r1, #0x2000; bl #0x2d602c; mov r8, r0
        ".word 0xe5850004, 0xe59f12bc, 0xe28f0faf, 0xe1a00000\n" // 0x00286d5c: str r0, [r5, #4]; ldr r1, [pc, #0x2bc]; add r0, pc, #0x2bc; mov r0, r0
        ".word 0xe3a01c01, 0xe1a03288, 0xe3a02000, 0xe1a00001\n" // 0x00286d6c: mov r1, #0x100; lsl r3, r8, #5; mov r2, #0; mov r0, r1
        ".word 0xe58d6000, 0xeb00f77f, 0xe5850000, 0xe3a00000\n" // 0x00286d7c: str r6, [sp]; bl #0x2c4b84; str r0, [r5]; mov r0, #0
        ".word 0xe58d0008, 0xe58d000c, 0xe5951014, 0xe5950054\n" // 0x00286d8c: str r0, [sp, #8]; str r0, [sp, #0xc]; ldr r1, [r5, #0x14]; ldr r0, [r5, #0x54]
        ".word 0xe3a09000, 0xe1a04009, 0xe5911008, 0xe3500000\n" // 0x00286d9c: mov sb, #0; mov r4, sb; ldr r1, [r1, #8]; cmp r0, #0
        ".word 0xe58d1000, 0x15900008, 0x158d0008, 0xe59500a4\n" // 0x00286dac: str r1, [sp]; ldrne r0, [r0, #8]; strne r0, [sp, #8]; ldr r0, [r5, #0xa4]
        ".word 0xe3500000, 0x15900008, 0x158d000c, 0xe585703c\n" // 0x00286dbc: cmp r0, #0; ldrne r0, [r0, #8]; strne r0, [sp, #0xc]; str r7, [r5, #0x3c]
        ".word 0xe1c564b6, 0xe585605c, 0xe5856060, 0xe5856064\n" // 0x00286dcc: strh r6, [r5, #0x46]; str r6, [r5, #0x5c]; str r6, [r5, #0x60]; str r6, [r5, #0x64]
        ".word 0xe5856068, 0xe585606c, 0xe5856070, 0xe5856074\n" // 0x00286ddc: str r6, [r5, #0x68]; str r6, [r5, #0x6c]; str r6, [r5, #0x70]; str r6, [r5, #0x74]
        ".word 0xe5856078, 0xe585607c, 0xe5856080, 0xe5856084\n" // 0x00286dec: str r6, [r5, #0x78]; str r6, [r5, #0x7c]; str r6, [r5, #0x80]; str r6, [r5, #0x84]
        ".word 0xe5856088, 0xe1a00005, 0xe585608c, 0xe3580000\n" // 0x00286dfc: str r6, [r5, #0x88]; mov r0, r5; str r6, [r5, #0x8c]; cmp r8, #0
        ".word 0xe5856090, 0xe5806094, 0x859fb240, 0x859fa200\n" // 0x00286e0c: str r6, [r5, #0x90]; str r6, [r0, #0x94]; ldrhi fp, [pc, #0x240]; ldrhi sl, [pc, #0x200]
        ".word 0xe5856098, 0xe1c564b8, 0xed858a13, 0x9a000106\n" // 0x00286e1c: str r6, [r5, #0x98]; strh r6, [r5, #0x48]; vstr s16, [r5, #0x4c]; bls #0x287248
        ".word 0xe5950000, 0xe0807284, 0xe08a0084, 0xe1d000b0\n" // 0x00286e2c: ldr r0, [r5]; add r7, r0, r4, lsl #5; add r0, sl, r4, lsl #1; ldrh r0, [r0]
        ".word 0xe6bf0fb0, 0xe1a06000, 0xe2400cff, 0xe25000ff\n" // 0x00286e3c: rev16 r0, r0; mov r6, r0; sub r0, r0, #0xff00; subs r0, r0, #0xff
        ".word 0xe1c760b0, 0x0a0000fc, 0xe3590000, 0x0a000003\n" // 0x00286e4c: strh r6, [r7]; beq #0x287248; cmp sb, #0; beq #0x286e6c
        ".word 0xe3560000, 0x03a09000, 0x0a0000f4, 0xea000001\n" // 0x00286e5c: cmp r6, #0; moveq sb, #0; beq #0x28723c; b #0x286e74
        ".word 0xe3560000, 0x059f61e8, 0xe1a00006, 0xeb009e0c\n" // 0x00286e6c: cmp r6, #0; ldreq r6, [pc, #0x1e8]; mov r0, r6; bl #0x2ae6b0
        ".word 0xe3500000, 0xe320f000, 0x0a000011, 0xe59f01d4\n" // 0x00286e7c: cmp r0, #0; nop ; beq #0x286ed0; ldr r0, [pc, #0x1d4]
        ".word 0xe1560000, 0xe0461000, 0x03a00001, 0x0a0000cc\n" // 0x00286e8c: cmp r6, r0; sub r1, r6, r0; moveq r0, #1; beq #0x2871d0
        ".word 0xca000090, 0xe59f01c0, 0xe1560000, 0xe0461000\n" // 0x00286e9c: bgt #0x2870e4; ldr r0, [pc, #0x1c0]; cmp r6, r0; sub r1, r6, r0
        ".word 0x03a09001, 0x0a0000e1, 0xca00007b, 0xe2460b3e\n" // 0x00286eac: moveq sb, #1; beq #0x28723c; bgt #0x2870a8; sub r0, r6, #0xf800
        ".word 0xe2500002, 0x0a000098, 0xe3500002, 0x1a00007a\n" // 0x00286ebc: subs r0, r0, #2; beq #0x287128; cmp r0, #2; bne #0x2870b8
        ".word 0xea00008e, 0xe59d0004, 0xe3500002, 0x0a000019\n" // 0x00286ecc: b #0x28710c; ldr r0, [sp, #4]; cmp r0, #2; beq #0x286f44
        ".word 0xe3590000, 0x0a00002f, 0xe59d0008, 0xe3500000\n" // 0x00286edc: cmp sb, #0; beq #0x286fa4; ldr r0, [sp, #8]; cmp r0, #0
        ".word 0x0a0000d2, 0xe5900000, 0xe1a01006, 0xe5902044\n" // 0x00286eec: beq #0x28723c; ldr r0, [r0]; mov r1, r6; ldr r2, [r0, #0x44]
        ".word 0xe59d0008, 0xe12fff32, 0xe3500000, 0x059f015c\n" // 0x00286efc: ldr r0, [sp, #8]; blx r2; cmp r0, #0; ldreq r0, [pc, #0x15c]
        ".word 0xe2871004, 0x01d060b2, 0xe59d0008, 0xe1a02006\n" // 0x00286f0c: add r1, r7, #4; ldrheq r6, [r0, #2]; ldr r0, [sp, #8]; mov r2, r6
        ".word 0xe5900000, 0xe5903040, 0xe59d0008, 0xe12fff33\n" // 0x00286f1c: ldr r0, [r0]; ldr r3, [r0, #0x40]; ldr r0, [sp, #8]; blx r3
        ".word 0xe5950054, 0xe1a01006, 0xebff047d, 0xe587001c\n" // 0x00286f2c: ldr r0, [r5, #0x54]; mov r1, r6; bl #0x248130; str r0, [r7, #0x1c]
        ".word 0xe320f000, 0xea0000bd, 0xe59d000c, 0xe3500000\n" // 0x00286f3c: nop ; b #0x28723c; ldr r0, [sp, #0xc]; cmp r0, #0
        ".word 0x0a0000ba, 0xe5900000, 0xe1a01006, 0xe5902044\n" // 0x00286f4c: beq #0x28723c; ldr r0, [r0]; mov r1, r6; ldr r2, [r0, #0x44]
        ".word 0xe59d000c, 0xe12fff32, 0xe3500000, 0x059f00fc\n" // 0x00286f5c: ldr r0, [sp, #0xc]; blx r2; cmp r0, #0; ldreq r0, [pc, #0xfc]
        ".word 0xe2871004, 0x01d060b2, 0xe59d000c, 0xe1a02006\n" // 0x00286f6c: add r1, r7, #4; ldrheq r6, [r0, #2]; ldr r0, [sp, #0xc]; mov r2, r6
        ".word 0xe5900000, 0xe5903040, 0xe59d000c, 0xe12fff33\n" // 0x00286f7c: ldr r0, [r0]; ldr r3, [r0, #0x40]; ldr r0, [sp, #0xc]; blx r3
        ".word 0xe59500a4, 0xe1a01006, 0xebff0465, 0xe587001c\n" // 0x00286f8c: ldr r0, [r5, #0xa4]; mov r1, r6; bl #0x248130; str r0, [r7, #0x1c]
        ".word 0xe320f000, 0xea0000a5, 0xe59d0000, 0xe1a01006\n" // 0x00286f9c: nop ; b #0x28723c; ldr r0, [sp]; mov r1, r6
        ".word 0xe5900000, 0xe5902044, 0xe59d0000, 0xe12fff32\n" // 0x00286fac: ldr r0, [r0]; ldr r2, [r0, #0x44]; ldr r0, [sp]; blx r2
        ".word 0xe3500000, 0x059f00a4, 0x01d060b2, 0xe59f009c\n" // 0x00286fbc: cmp r0, #0; ldreq r0, [pc, #0xa4]; ldrheq r6, [r0, #2]; ldr r0, [pc, #0x9c]
        ".word 0xe5900020, 0xe3500000, 0x0a000026, 0xe1500006\n" // 0x00286fcc: ldr r0, [r0, #0x20]; cmp r0, #0; beq #0x287074; cmp r0, r6
        ".word 0x1a000024, 0xe59d0000, 0xe59f6084, 0xe2871004\n" // 0x00286fdc: bne #0x287074; ldr r0, [sp]; ldr r6, [pc, #0x84]; add r1, r7, #4
        ".word 0xe5900000, 0xe1a02006, 0xe5903040, 0xe59d0000\n" // 0x00286fec: ldr r0, [r0]; mov r2, r6; ldr r3, [r0, #0x40]; ldr r0, [sp]
        ".word 0xe12fff33, 0xe5950014, 0xe1a01006, 0xebff0448\n" // 0x00286ffc: blx r3; ldr r0, [r5, #0x14]; mov r1, r6; bl #0x248130
        ".word 0xe587001c, 0xe320f000, 0xea000088, 0x00000000\n" // 0x0028700c: str r0, [r7, #0x1c]; nop ; b #0x28723c; andeq r0, r0, r0
        ".word 0x004daf08, 0x004dcf08, 0x0000018b, 0x535c3a63\n" // 0x0028701c: subeq sl, sp, r8, lsl #30; subeq ip, sp, r8, lsl #30; andeq r0, r0, fp, lsl #3; cmppl ip, #0x63000
        ".word 0x5c34544d, 0x36445258, 0x415c3638, 0x44536473\n" // 0x0028702c: ldcpl p4, c5, [r4], #-0x134; literal/data; literal/data; literal/data
        ".word 0x6f535c4b, 0x65637275, 0x7866475c, 0x7865545c\n" // 0x0028703c: literal/data; literal/data; literal/data; literal/data
        ".word 0x73415c74, 0x78655464, 0x70632e74, 0x00000070\n" // 0x0028704c: literal/data; literal/data; literal/data; literal/data
        ".word 0x004daee8, 0x00008260, 0x0000f816, 0x0000f812\n" // 0x0028705c: literal/data; literal/data; literal/data; literal/data
        ".word 0x00464d48, 0x00008140, 0xe59d0000, 0xe1a02006\n" // 0x0028706c: literal/data; literal/data; literal/data; literal/data
        ".word 0xe2871004, 0xe5900000, 0xe5903040, 0xe59d0000\n" // 0x0028707c: literal/data; literal/data; literal/data; literal/data
        ".word 0xe12fff33, 0xe5950014, 0xe1a01006, 0xebff0424\n" // 0x0028708c: literal/data; literal/data; literal/data; literal/data
        ".word 0xe587001c, 0xe320f000, 0xea000064, 0xe3510001\n" // 0x0028709c: literal/data; literal/data; literal/data; literal/data
        ".word 0x0a000021, 0xe3510002, 0x0a000038, 0xe59f11d0\n" // 0x002870ac: literal/data; literal/data; literal/data; literal/data
        ".word 0xe3a00000, 0xe79b2100, 0xe3520000, 0x0a000042\n" // 0x002870bc: literal/data; literal/data; literal/data; literal/data
        ".word 0xe0812080, 0xe1d230b0, 0xe1530006, 0x1a00003e\n" // 0x002870cc: literal/data; literal/data; literal/data; literal/data
        ".word 0xe3a00000, 0xea000040, 0xe3510001, 0x03a00002\n" // 0x002870dc: literal/data; literal/data; literal/data; literal/data
        ".word 0x0a000037, 0xe3510002, 0x03a00000, 0x058d0004\n" // 0x002870ec: literal/data; literal/data; literal/data; literal/data
        ".word 0x0a00004e, 0xe3510003, 0x13510004, 0x1affffea\n" // 0x002870fc: literal/data; literal/data; literal/data; literal/data
        ".word 0xe2844001, 0xe5950000, 0xe08a1084, 0xe1d110b0\n" // 0x0028710c: literal/data; literal/data; literal/data; literal/data
        ".word 0xe0800284, 0xe1c010b0, 0xea000044, 0xe595003c\n" // 0x0028711c: literal/data; literal/data; literal/data; literal/data
        ".word 0xe2801001, 0xe585103c, 0xea000040, 0xe2841001\n" // 0x0028712c: literal/data; literal/data; literal/data; literal/data
        ".word 0xe5952000, 0xe08a0081, 0xe1d000b0, 0xe0822281\n" // 0x0028713c: literal/data; literal/data; literal/data; literal/data
        ".word 0xe2841002, 0xe1c200b0, 0xe5952000, 0xe08a0081\n" // 0x0028714c: literal/data; literal/data; literal/data; literal/data
        ".word 0xe1d000b0, 0xe0822281, 0xe2841003, 0xe1c200b0\n" // 0x0028715c: literal/data; literal/data; literal/data; literal/data
        ".word 0xe5952000, 0xe08a0081, 0xe2844004, 0xe1d000b0\n" // 0x0028716c: literal/data; literal/data; literal/data; literal/data
        ".word 0xe0822281, 0xe08a1084, 0xe1c200b0, 0xe5950000\n" // 0x0028717c: literal/data; literal/data; literal/data; literal/data
        ".word 0xe1d110b0, 0xe0800284, 0xe1c010b0, 0xea000027\n" // 0x0028718c: literal/data; literal/data; literal/data; literal/data
        ".word 0xe2842001, 0xe5950000, 0xe08a1082, 0xe2844002\n" // 0x0028719c: literal/data; literal/data; literal/data; literal/data
        ".word 0xe1d110b0, 0xe0800282, 0xe1c010b0, 0xe5950000\n" // 0x002871ac: literal/data; literal/data; literal/data; literal/data
        ".word 0xe08a1084, 0xe1d110b0, 0xe0800284, 0xe1c010b0\n" // 0x002871bc: literal/data; literal/data; literal/data; literal/data
        ".word 0xea00001a, 0xe58d0004, 0xea000018, 0xe2800001\n" // 0x002871cc: literal/data; literal/data; literal/data; literal/data
        ".word 0xe3500008, 0xbaffffb6, 0xea000014, 0xe79b2100\n" // 0x002871dc: literal/data; literal/data; literal/data; literal/data
        ".word 0xe3520000, 0x0a000018, 0xe0812080, 0xe1d220b0\n" // 0x002871ec: literal/data; literal/data; literal/data; literal/data
        ".word 0xe1520006, 0x1a000014, 0xe59f1088, 0xe7911100\n" // 0x002871fc: literal/data; literal/data; literal/data; literal/data
        ".word 0xe3a00000, 0xe3510000, 0xda000008, 0xe2844001\n" // 0x0028720c: literal/data; literal/data; literal/data; literal/data
        ".word 0xe5952000, 0xe08a3084, 0xe2800001, 0xe1d330b0\n" // 0x0028721c: literal/data; literal/data; literal/data; literal/data
        ".word 0xe0822284, 0xe1510000, 0xe1c230b0, 0xcafffff6\n" // 0x0028722c: literal/data; literal/data; literal/data; literal/data
        ".word 0xe2844001, 0xe1540008, 0x3afffef8, 0xe59d0024\n" // 0x0028723c: literal/data; literal/data; literal/data; literal/data
        ".word 0xe3700001, 0x1a000009, 0xea000003, 0xe2800001\n" // 0x0028724c: literal/data; literal/data; literal/data; literal/data
        ".word 0xe3500008, 0xbaffffe0, 0xeafffff4, 0xe1a00005\n" // 0x0028725c: literal/data; literal/data; literal/data; literal/data
        ".word 0xeb00b049, 0xe3500000, 0xe320f000, 0x0afffffa\n" // 0x0028726c: literal/data; literal/data; literal/data; literal/data
        ".word 0xe28dd014, 0xecbd8b02, 0xe28dd010, 0xe8bd4ff0\n" // 0x0028727c: literal/data; literal/data; literal/data; literal/data
        ".word 0xeafe2579, 0x004def18, 0x004def28\n" // 0x0028728c: literal/data; literal/data; literal/data
    );
}

[[maybe_unused]] static void AsdText_func_00296de0_Decompiled(
    AsdText* text, s32 font_id, s32 mode, s32 width, s32 height,
    const char* utf8)
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

// The C reconstruction above documents the converter's scratch-state and
// terminator behavior; this ARM body preserves the original call/stack layout.
// DECOMP_FUNC(0x00296de0, 280)
__attribute__((naked)) void AsdText_func_00296de0(
    AsdText*, s32, s32, s32, s32, const char*)
{
    asm volatile(
        ".word 0xe92d43f0, 0xe1a05000, 0xe1a06001, 0xe1a07002\n" // 0x00296de0: push {r4, r5, r6, r7, r8, sb, lr}; mov r5, r0; mov r6, r1; mov r7, r2
        ".word 0xe1a08003, 0xed2d8b02, 0xe24dd00c, 0xe3a010d5\n" // 0x00296df0: mov r8, r3; vpush {d8}; sub sp, sp, #0xc; mov r1, #0xd5
        ".word 0xed9d8a0c, 0xe28f00b4, 0xe1a00000, 0xe3a09000\n" // 0x00296e00: vldr s16, [sp, #0x30]; add r0, pc, #0xb4; mov r0, r0; mov sb, #0
        ".word 0xe3a01c01, 0xe3a03a01, 0xe1a02009, 0xe1a00001\n" // 0x00296e10: mov r1, #0x100; mov r3, #0x1000; mov r2, sb; mov r0, r1
        ".word 0xe58d9000, 0xeb00b756, 0xe1a04000, 0xe59d0034\n" // 0x00296e20: str sb, [sp]; bl #0x2c4b84; mov r4, r0; ldr r0, [sp, #0x34]
        ".word 0xeb00b116, 0xe59d2034, 0xe28d3038, 0xe3a01a01\n" // 0x00296e30: bl #0x2c3290; ldr r2, [sp, #0x34]; add r3, sp, #0x38; mov r1, #0x1000
        ".word 0xe1a00004, 0xfa006dca, 0xe1a00004, 0xe5c49fff\n" // 0x00296e40: mov r0, r4; blx #0x2b2574; mov r0, r4; strb sb, [r4, #0xfff]
        ".word 0xeb00b10e, 0xe59f2098, 0xe1a01000, 0xe3e00000\n" // 0x00296e50: bl #0x2c3290; ldr r2, [pc, #0x98]; mov r1, r0; mvn r0, #0
        ".word 0xe1510002, 0x3a000004, 0xe5c40ffc, 0xe5c40ffd\n" // 0x00296e60: cmp r1, r2; blo #0x296e7c; strb r0, [r4, #0xffc]; strb r0, [r4, #0xffd]
        ".word 0xe5c40ffe, 0xe5c49fff, 0xea000004, 0xe0842001\n" // 0x00296e70: strb r0, [r4, #0xffe]; strb sb, [r4, #0xfff]; b #0x296e90; add r2, r4, r1
        ".word 0xe7c40001, 0xe5c20001, 0xe5c20002, 0xe5c29003\n" // 0x00296e80: strb r0, [r4, r1]; strb r0, [r2, #1]; strb r0, [r2, #2]; strb sb, [r2, #3]
        ".word 0xed8d8a00, 0xe1a03008, 0xe1a02007, 0xe1a01006\n" // 0x00296e90: vstr s16, [sp]; mov r3, r8; mov r2, r7; mov r1, r6
        ".word 0xe1a00005, 0xe58d4004, 0xebffbf6b, 0xe28dd00c\n" // 0x00296ea0: mov r0, r5; str r4, [sp, #4]; bl #0x286c5c; add sp, sp, #0xc
        ".word 0xe1a00004, 0xecbd8b02, 0xe8bd43f0, 0xea00b527\n" // 0x00296eb0: mov r0, r4; vpop {d8}; pop {r4, r5, r6, r7, r8, sb, lr}; b #0x2c4360
        ".word 0x535c3a63, 0x5c34544d, 0x36445258, 0x415c3638\n" // 0x00296ec0: cmppl ip, #0x63000; ldcpl p4, c5, [r4], #-0x134; literal/data; literal/data
        ".word 0x44536473, 0x6f535c4b, 0x65637275, 0x7866475c\n" // 0x00296ed0: literal/data; literal/data; literal/data; literal/data
        ".word 0x7865545c, 0x73415c74, 0x78655464, 0x70632e74\n" // 0x00296ee0: literal/data; literal/data; literal/data; literal/data
        ".word 0x00000070, 0x00000ffd\n" // 0x00296ef0: literal/data; literal/data
    );
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

[[maybe_unused]] static void AsdListBox_func_0025c550_Decompiled(
    void* handle, const AsdListBoxEntry* entries, s32 count)
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

// Keep the descriptor switch and link semantics above; retain the ARM jump
// table, floating-point cases, and literals for byte-exact matching.
// DECOMP_FUNC(0x0025c550, 628)
__attribute__((naked)) void AsdListBox_func_0025c550(
    void*, const AsdListBoxEntry*, s32)
{
    asm volatile(
        ".word 0xe92d4ff7, 0xe1a07000, 0xe3a08000, 0xe1a0b001\n" // 0x0025c550: push {r0, r1, r2, r4, r5, r6, r7, r8, sb, sl, fp, lr}; mov r7, r0; mov r8, #0; mov fp, r1
        ".word 0xed2d8b04, 0xe24dd008, 0xe59d0020, 0xe3500000\n" // 0x0025c560: vpush {d8, d9}; sub sp, sp, #8; ldr r0, [sp, #0x20]; cmp r0, #0
        ".word 0xc3a09001, 0xda00008b, 0xe08b5288, 0xe1a00007\n" // 0x0025c570: movgt sb, #1; ble #0x25c7a8; add r5, fp, r8, lsl #5; mov r0, r7
        ".word 0xe595a000, 0xeb01914f, 0xe1a04000, 0xe59f1224\n" // 0x0025c580: ldr sl, [r5]; bl #0x2c0ac8; mov r4, r0; ldr r1, [pc, #0x224]
        ".word 0xe59f0224, 0xe1a00000, 0xe3a01c01, 0xe3a03e22\n" // 0x0025c590: ldr r0, [pc, #0x224]; mov r0, r0; mov r1, #0x100; mov r3, #0x220
        ".word 0xe3a02000, 0xe1a00001, 0xe58d9000, 0xeb01a174\n" // 0x0025c5a0: mov r2, #0; mov r0, r1; str sb, [sp]; bl #0x2c4b84
        ".word 0xe1a06000, 0xe3a02c01, 0xe1a0100a, 0xe2800006\n" // 0x0025c5b0: mov r6, r0; mov r2, #0x100; mov r1, sl; add r0, r0, #6
        ".word 0xeb001966, 0xe3a0a000, 0xe5c6a004, 0xe5940070\n" // 0x0025c5c0: bl #0x262b60; mov sl, #0; strb sl, [r6, #4]; ldr r0, [r4, #0x70]
        ".word 0xe59f21e8, 0xe1a01006, 0xe5860000, 0xe5940070\n" // 0x0025c5d0: ldr r2, [pc, #0x1e8]; mov r1, r6; str r0, [r6]; ldr r0, [r4, #0x70]
        ".word 0xe2800001, 0xe5840070, 0xe1a00004, 0xeb015888\n" // 0x0025c5e0: add r0, r0, #1; str r0, [r4, #0x70]; mov r0, r4; bl #0x2b2814
        ".word 0xe1a00007, 0xe320f000, 0xebfff5e2, 0xe284000c\n" // 0x0025c5f0: mov r0, r7; nop ; bl #0x259d88; add r0, r4, #0xc
        ".word 0xe320f000, 0xeb01e41c, 0xe284000c, 0xe320f000\n" // 0x0025c600: nop ; bl #0x2d567c; add r0, r4, #0xc; nop
        ".word 0xe590001c, 0xe584006c, 0xe5d50004, 0xe5964000\n" // 0x0025c610: ldr r0, [r0, #0x1c]; str r0, [r4, #0x6c]; ldrb r0, [r5, #4]; ldr r4, [r6]
        ".word 0xe3500005, 0x379ff100, 0xea000052, 0x0025c778\n" // 0x0025c620: cmp r0, #5; ldrlo pc, [pc, r0, lsl #2]; b #0x25c778; eoreq ip, r5, r8, ror r7
        ".word 0x0025c640, 0x0025c690, 0x0025c6e0, 0x0025c734\n" // 0x0025c630: eoreq ip, r5, r0, asr #12; mlaeq r5, r0, r6, ip; eoreq ip, r5, r0, ror #13; eoreq ip, r5, r4, lsr r7
        ".word 0xe5956008, 0xe1a01004, 0xe1a00007, 0xebffe267\n" // 0x0025c640: ldr r6, [r5, #8]; mov r1, r4; mov r0, r7; bl #0x254ff0
        ".word 0xe3500000, 0xe320f000, 0x0a000046, 0xe3560000\n" // 0x0025c650: cmp r0, #0; nop ; beq #0x25c778; cmp r6, #0
        ".word 0xe5c09004, 0x0a000004, 0xe2800c01, 0xe3a02c01\n" // 0x0025c660: strb sb, [r0, #4]; beq #0x25c67c; add r0, r0, #0x100; mov r2, #0x100
        ".word 0xe1a01006, 0xe2800006, 0xeb001938, 0xe1a00007\n" // 0x0025c670: mov r1, r6; add r0, r0, #6; bl #0x262b60; mov r0, r7
        ".word 0xebfff5c0, 0xe320f000, 0xe320f000, 0xea000039\n" // 0x0025c680: bl #0x259d88; nop ; nop ; b #0x25c778
        ".word 0xe595000c, 0xe1a01004, 0xe3500000, 0x13a06001\n" // 0x0025c690: ldr r0, [r5, #0xc]; mov r1, r4; cmp r0, #0; movne r6, #1
        ".word 0x03a06000, 0xe1a00007, 0xebffe250, 0xe3500000\n" // 0x0025c6a0: moveq r6, #0; mov r0, r7; bl #0x254ff0; cmp r0, #0
        ".word 0xe320f000, 0x0a00002f, 0xe3a01002, 0xe5c01004\n" // 0x0025c6b0: nop ; beq #0x25c778; mov r1, #2; strb r1, [r0, #4]
        ".word 0xe5a06208, 0xe5a0a008, 0xe5809004, 0xe1a00007\n" // 0x0025c6c0: str r6, [r0, #0x208]!; str sl, [r0, #8]!; str sb, [r0, #4]; mov r0, r7
        ".word 0xebfff5ac, 0xe320f000, 0xe320f000, 0xea000025\n" // 0x0025c6d0: bl #0x259d88; nop ; nop ; b #0x25c778
        ".word 0xe2850010, 0xe5d56018, 0xe1a01004, 0xec908a02\n" // 0x0025c6e0: add r0, r5, #0x10; ldrb r6, [r5, #0x18]; mov r1, r4; vldmia r0, {s16, s17}
        ".word 0xe1a00007, 0xed959a03, 0xebffe23c, 0xe3500000\n" // 0x0025c6f0: mov r0, r7; vldr s18, [r5, #0xc]; bl #0x254ff0; cmp r0, #0
        ".word 0xe320f000, 0x0a00001b, 0xe3a01003, 0xed809a82\n" // 0x0025c700: nop ; beq #0x25c778; mov r1, #3; vstr s18, [r0, #0x208]
        ".word 0xe5c01004, 0xe2801e21, 0xec818a02, 0xe5c06005\n" // 0x0025c710: strb r1, [r0, #4]; add r1, r0, #0x210; vstmia r1, {s16, s17}; strb r6, [r0, #5]
        ".word 0xe1a00007, 0xebfff597, 0xe320f000, 0xe320f000\n" // 0x0025c720: mov r0, r7; bl #0x259d88; nop ; nop
        ".word 0xea000010, 0xed950a03, 0xe2852010, 0xe1a01004\n" // 0x0025c730: b #0x25c778; vldr s0, [r5, #0xc]; add r2, r5, #0x10; mov r1, r4
        ".word 0xeeb88ac0, 0xecd28a02, 0xe1a00007, 0xebffe227\n" // 0x0025c740: vcvt.f32.s32 s16, s0; vldmia r2, {s17, s18}; mov r0, r7; bl #0x254ff0
        ".word 0xe3500000, 0xe320f000, 0x0a000006, 0xe2802f83\n" // 0x0025c750: cmp r0, #0; nop ; beq #0x25c778; add r2, r0, #0x20c
        ".word 0xe3a01004, 0xec828a02, 0xe5c01004, 0xed809a85\n" // 0x0025c760: mov r1, #4; vstmia r2, {s16, s17}; strb r1, [r0, #4]; vstr s18, [r0, #0x214]
        ".word 0xe1a00007, 0xebfff583, 0xe595501c, 0xe3550000\n" // 0x0025c770: mov r0, r7; bl #0x259d88; ldr r5, [r5, #0x1c]; cmp r5, #0
        ".word 0x0a000004, 0xe1a00007, 0xe1a01004, 0xebffe217\n" // 0x0025c780: beq #0x25c798; mov r0, r7; mov r1, r4; bl #0x254ff0
        ".word 0xe3500000, 0x1580521c, 0xe59d0020, 0xe2888001\n" // 0x0025c790: cmp r0, #0; strne r5, [r0, #0x21c]; ldr r0, [sp, #0x20]; add r8, r8, #1
        ".word 0xe1580000, 0xbaffff73, 0xe28dd008, 0xecbd8b04\n" // 0x0025c7a0: cmp r8, r0; blt #0x25c578; add sp, sp, #8; vpop {d8, d9}
        ".word 0xe28dd00c, 0xe8bd8ff0, 0x000003f3, 0x00409bb0\n" // 0x0025c7b0: add sp, sp, #0xc; pop {r4, r5, r6, r7, r8, sb, sl, fp, pc}; strdeq r0, r1, [r0], -r3; strheq sb, [r0], #-0xb0
        ".word 0x002e117c\n" // 0x0025c7c0: eoreq r1, lr, ip, ror r1
    );
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
