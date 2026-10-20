#include "ui/ui_runtime.h"
#include "engine/asd_symbols.h"
#include "script/script_extras.h"
#include <cstring>

namespace smt4::ui {

using engine::Npc2dLayoutNode;

UiPartRenderState g_UiPartRenderState{};        // 0x004EA81C (BSS)

namespace {

// ---------------------------------------------------------------------------
// Shared ABI declarations (one per binary address; canonical spellings).
// ---------------------------------------------------------------------------

extern "C" {
    extern u8* g_AsdGpuState;                                                   // 0x0044EA00

    void* Camp_GetMainWork();                                                   // 0x00262a44
    s32   UiAnimSprite_GetPosX(const UiAnimSprite* sprite);                     // 0x002bef7c
    s32   UiAnimSprite_GetPosY(const UiAnimSprite* sprite);                     // 0x002bef70
    f32   UiGpu_TransformCoord(u8* gpu_state, f32 scale);                       // 0x002ba46c
    void  UiSprite_DrawNode(u32 screen, u32 group, u32 node,
                            s32 x, s32 y, s32 prio);                            // 0x002bf460
    void  UiSprite_DrawPanel(u32 screen, u32 group, u32 panel,
                             s32 x, s32 y, s32 prio);                           // 0x002bf558
    const Npc2dLayoutNode* UiLayout_GetNode(u32 group, u32 node);               // 0x002bf6d0
    void  UiFont_FormatString(char* dst, const char* fmt, ...);                 // 0x002be7fc
    void  UiFont_DrawText(u32 font_id, u32 rgba, const char* text,
                          f32 x, f32 y, f32 scale_x, f32 rot, f32 scale_y);     // 0x002be77c
    void  UiFont_DrawFormatted(u32 screen, s32 x, s32 y, s32 mode, s32 width,
                               s32 prio, const char* fmt, s32 value);           // 0x002be16c
    void  UiSprite_SetGlobalAlpha(f32 alpha);                                   // 0x002bf710

    s32   UiListCursor_GetRowCount(const UiListCursor* cursor);                 // 0x0029f0f4
    s32   UiListCursor_GetSelectedRow(const UiListCursor* cursor);              // 0x0029f248
    s32   UiListCursor_GetScrollOffset(const UiListCursor* cursor);             // 0x0029f260
    void  UiListCursor_InitFromRow(u16 row_id, UiListCursor* cursor);           // 0x0029df14
    s32   UiListCursor_CountPartySlots(const UiListCursor* cursor);             // 0x0029cb94
    s32   UiList_CountActiveRows(const void* list);                             // 0x0029d8e4

    void  UiFont_DrawFormattedEx(u32 screen, s32 x, s32 y, s32 align,
                                 s32 color, u32 size, const char* fmt,
                                 s32 value);                                    // 0x002be16c

    s32   UiArray_ContainsU16(const u16* values, s32 count, u16 value);         // 0x0029d080
    s32   UiTouch_GetRegionTouchState(s16 handle);                              // 0x0029d8fc
    void  UiScissor_SetRect(s32 x, s32 y, s32 w, s32 h, s32 enable);            // 0x0029a418
    void  UiScrollBar_Draw(UiListCursor* cursor, s32 x, s32 y, u32 group,
                           s32 up_h, s32 down_h, s32 a6, s32 a7, s32 a8,
                           s32 a9, s32 a10, s32 btn_h, s32 up_h2,
                           s32 down_h2, s32 prio, s32 a15);                     // 0x00290c38

    void  UiSkill_DrawItemIconAndCount(s32 item_id, s32 x, s32 y,
                                       s32 prio, s32 a4);                       // 0x002b6a98
    void  UiParty_DrawDemonBars(s16 demon_id, s32 x, s32 y, s32 prio,
                                f32 scale, s32 a5);                             // 0x002b6f74
    s32   Party_GetDemonActiveIndex(s16 demon_id);                              // 0x0029abc0
    const char* Item_GetNameString(u16 item_id);                                // 0x002bcff0
    const char* Item_GetShortNameString(u16 item_id);                           // 0x002bd258
    const char* Item_GetDescriptionString(u16 item_id);                         // 0x002bd020

    // Quest UI helpers (0x00197D2C call graph).
    void* Quest_GetRow(u16 quest_id);                                           // 0x002b6700
    bool  Quest_IsNew(u16 quest_id);                                            // 0x002990bc
    bool  Quest_IsCompleted(u16 quest_id);                                      // 0x00299084
    bool  Quest_IsExpired(u16 quest_id);                                        // 0x0028f460
    bool  Quest_IsRewardKnown(u16 quest_id);                                    // 0x0028f5a8
    const char* Quest_GetTitle(u16 quest_id);                                   // 0x002bcfcc
    const char* Quest_GetDescription(u16 quest_id);                             // 0x0011b374
    const char* Quest_GetObjectiveName(u16 entry_id);                           // 0x002be828
    const char* Quest_GetRewardItemName(u16 item_id);                           // 0x00333be8
    const u8* Quest_GetFlagTable();                                             // 0x002adf14
    s32   Quest_GetTrackedId();                                                 // 0x00290694
    void  Quest_DrawObjectiveIcon(u16 entry_id, s32 x, s32 y, s32 prio);        // 0x002be548
    void  Quest_DrawIcon(u16 quest_id, s32 x, s32 y, s32 prio);                 // 0x0029af60
    f32   Quest_MeasureText(const char* text, s32 mode);                        // 0x0028f758
    void  Quest_FormatReward(char* dst, u16 reward_id);                         // 0x00290a68
    bool  Quest_GetRewardEntry(u16 quest_id, s32 index, void* out);             // 0x002990dc
    void  Quest_DrawRewardRow(void* object, f32 value);                         // 0x002b9708
    void* Tbb_GetGlobalSubTable(u32 group, s32 index);                          // 0x002c0ec4
    void* Tbb_GetPayloadData(void* sub_table);                                  // 0x002c0e9c
    u32   Tbb_GetRowCount(void* sub_table);                                     // 0x002c0e4c

    // Common render helpers (0x00267FB0 call graph).
    void  UiPart_GetBufferAttrib(void* handle, s32 kind, void* out);            // 0x002575a8
    void  UiPart_GetVector(void* part, void* out);                              // 0x0024faa4
    void  UiPart_GetMatrix(void* part, void* out);                              // 0x0024fa94
    void  UiPart_GetSceneMatrix(void* out);                                     // 0x002a2f1c
    void* UiPart_EndScene(void* part);                                          // 0x00219780
    void* UiPart_SetupTexture(void* object, s32 mode);                          // 0x001e18dc
    void  UiPart_FlushTexture(void* object);                                    // 0x00269758
    void  UiPart_SubmitA(u32 handle, u32 color);                                // 0x001e1900
    void  UiPart_SubmitB(u32 handle);                                           // 0x0024c564
    void  UiPart_SubmitC(u32 handle, u32 color);                                // 0x002a37dc
    void  UiPart_SubmitD(u32 handle);                                           // 0x00281adc
    void  UiPart_DrawDirect(void* context);                                     // 0x002c7cc4
    void  UiPart_SetupParams(void* object);                                     // 0x002571c8
    void  UiPart_GetParams(void* object, void* out);                            // 0x00256ffc
    void  UiPart_PackUV(u32 handle);                                            // 0x0025741c
    void  UiPart_Submit(u32 handle, u16 id);                                    // 0x00256c90

    // Fusion/quest UI helpers.
    void  UiAnimSprite_DrawAt(u32 handle, s32 x, s32 y, s32 prio,
                              s32 frame, s32 index, f32 scale);                 // 0x002b792c
    void  Item_DrawDescriptionIcon(u16 item_id, s32 x, s32 y, s32 prio);        // 0x00258308
    void  Item_BuildFusionPairList(u16 item_id, u8 count, const u16* source,
                                   void* out, s32 mode);                        // 0x0026ac34
}

// ---------------------------------------------------------------------------
// 0x00267FB0 helpers
// ---------------------------------------------------------------------------

/** 0x001F1780 / 0x001F183C / 0x001F1854 and 0x001985A4..0x00198644 update
 *  the GPU state slot at `g_AsdGpuState + 0x12AC`: the low word is the ring
 *  cursor, the value is stored at +8+index*4 and the +0x1C callback runs when
 *  the slot changes or +0x18 is set. */
void GpuModeSlotSet(u32 value) {
    u8* slot = g_AsdGpuState + 0x1000 + 0x2AC;
    const u32 index = *reinterpret_cast<u32*>(slot);
    u32* entry = reinterpret_cast<u32*>(slot + 8 + index * 4);
    const u32 old = *entry;
    *entry = value;
    if (*reinterpret_cast<u8*>(slot + 0x18) != 0 || old != value) {
        reinterpret_cast<void (*)()>(
            *reinterpret_cast<u32*>(slot + 0x1C))();
        *reinterpret_cast<u8*>(slot + 0x18) = 0;
    }
}

/** 0x002575A8 fills {pointer, stride}; every loop advances the pointer by
 *  `stride` (`ldm r7,{r1,r2}` / `add r1,r1,r2`, 0x00268488..0x00268490). */
struct UiBufferCursor {
    u8* ptr;
    u32 stride;
};
static_assert(offsetof(UiBufferCursor, ptr) == 0x00);
static_assert(offsetof(UiBufferCursor, stride) == 0x04);
static_assert(sizeof(UiBufferCursor) == 0x08);

void Buffer_Advance(UiBufferCursor& cursor) {
    cursor.ptr += cursor.stride;
}

u32 FloatToByte(f32 value) {
    return static_cast<u32>(value * 255.0f);            // vcvt.u32.f32 + *1/255
}

/** ARGB word -> four floats in A,R,G,B order; the prologue at
 *  0x00267FC8..0x0026801C extracts the four bytes and scales by 1/255
 *  (0x3B808081). */
void UnpackColor(u32 color, f32 out[4]) {
    const f32 k = 0x3B808081u ? 0.0039215688593685627f : 0.0f;
    out[0] = static_cast<f32>((color >> 24) & 0xFF) * k;
    out[1] = static_cast<f32>((color >> 16) & 0xFF) * k;
    out[2] = static_cast<f32>((color >> 8) & 0xFF) * k;
    out[3] = static_cast<f32>(color & 0xFF) * k;
}

u32 PackColor(const f32 in[4]) {
    return (FloatToByte(in[0]) << 24) | (FloatToByte(in[1]) << 16) |
           (FloatToByte(in[2]) << 8) | FloatToByte(in[3]);
}

/** Column-major 4x4 * 4-vector; the multiply at 0x002681E4..0x00268278 reads
 *  matrix slots 0x00..0x3C and writes the result back through r2. */
void TransformVector(const f32 m[16], const f32 v[4], f32 out[4]) {
    out[0] = m[0] * v[0] + m[4] * v[1] + m[8] * v[2] + m[12] * v[3];
    out[1] = m[1] * v[0] + m[5] * v[1] + m[9] * v[2] + m[13] * v[3];
    out[2] = m[2] * v[0] + m[6] * v[1] + m[10] * v[2] + m[14] * v[3];
    out[3] = m[3] * v[0] + m[7] * v[1] + m[11] * v[2] + m[15] * v[3];
}

/** Signed bit-pattern wrap of an angle into (-pi, pi].  The listing compares
 *  the raw float word against 0x40490FDB / 0xC0490FDB and adds/subtracts
 *  0x40C90FDB in a loop (0x002682E8..0x002684CC, 0x00268A6C..0x00268E40). */
f32 NormalizeAngle(f32 angle) {
    const s32 pi_bits     = static_cast<s32>(0x40490FDBu);
    const s32 neg_pi_bits = static_cast<s32>(0xC0490FDBu);
    const f32 two_pi      = 6.2831854820251465f;        // 0x40C90FDB

    u32 bits;
    std::memcpy(&bits, &angle, sizeof(bits));
    if (static_cast<s32>(bits) > pi_bits) {
        do {
            angle -= two_pi;
            std::memcpy(&bits, &angle, sizeof(bits));
        } while (static_cast<s32>(bits) > pi_bits);
    } else if (static_cast<s32>(bits) < neg_pi_bits) {
        do {
            angle += two_pi;
            std::memcpy(&bits, &angle, sizeof(bits));
        } while (static_cast<s32>(bits) > neg_pi_bits);
    }
    return angle;
}

/** Collect one entry into the four interleaved cursors built by
 *  0x002575A8: position (3 floats), colour (1 word), rotation (1 float) and
 *  scale (2 floats). */
void EmitEntry(const UiPartEntry& entry, UiBufferCursor& pos,
               UiBufferCursor& color, UiBufferCursor& rot,
               UiBufferCursor& scale_cursor, f32 scale_x, f32 scale_y,
               bool apply_entry_scale) {
    f32* p = reinterpret_cast<f32*>(pos.ptr);
    p[0] = entry.vector[0];
    p[1] = entry.vector[1];
    p[2] = entry.vector[2];
    Buffer_Advance(pos);

    *reinterpret_cast<u32*>(color.ptr) = entry.color;
    Buffer_Advance(color);

    *reinterpret_cast<f32*>(rot.ptr) = entry.rotation;
    Buffer_Advance(rot);

    f32 sx = entry.scale * scale_x;
    f32 sy = entry.scale * scale_y;
    if (apply_entry_scale) {
        sx *= entry.scale_x;
        sy *= entry.scale_y;
    }
    f32* s = reinterpret_cast<f32*>(scale_cursor.ptr);
    s[0] = sx;
    s[1] = sy;
    Buffer_Advance(scale_cursor);
}

/** Common tail of the 1/4/9 and 2 render paths (0x00268554..0x00268604 and
 *  0x00268E54..0x00268EE8). */
void FinishPartDraw(UiPartRenderContext* ctx, s32 visible, bool copy_back) {
    if (visible == 0) {
        return;
    }
    u32 color = ctx->color;
    u8* sprite = static_cast<u8*>(ctx->sprite);
    u8* resource = *reinterpret_cast<u8**>(sprite + 0x0C);

    if (copy_back) {
        void* src = UiPart_EndScene(ctx->parts);        // 0x00219780
        if (src != nullptr) {
            u32 flags = *reinterpret_cast<u32*>(resource + 0xA8);
            *reinterpret_cast<u32*>(resource + 0xA8) = flags | 2;
            AsdMem_CopyFrom(src, resource + 0xAC, 8);   // 0x002bd610
        }
        *reinterpret_cast<u32*>(resource + 0x60) = static_cast<u32>(visible);
        *reinterpret_cast<u32*>(resource + 0x64) = color;
    } else {
        *reinterpret_cast<u32*>(resource + 0x64) = color;
        *reinterpret_cast<u32*>(resource + 0x60) = static_cast<u32>(visible);
    }

    u16 id = *reinterpret_cast<u16*>(ctx->parts->handle + 0x54);
    UiPart_PackUV(id);                                  // 0x0025741c
    UiPart_Submit(static_cast<u32>(reinterpret_cast<std::uintptr_t>(ctx->sprite)),
                  id);                                  // 0x00256c90
}

/** Prepare the four interleaved cursors for a part set. */
void AllocPartCursors(u32 handle, UiBufferCursor& pos, UiBufferCursor& color,
                      UiBufferCursor& rot, UiBufferCursor& scale_cursor) {
    UiPart_GetBufferAttrib(reinterpret_cast<void*>(handle), 1, &pos);
    UiPart_GetBufferAttrib(reinterpret_cast<void*>(handle), 2, &color);
    UiPart_GetBufferAttrib(reinterpret_cast<void*>(handle), 4, &scale_cursor);
    UiPart_GetBufferAttrib(reinterpret_cast<void*>(handle), 0x20, &rot);
}

} // namespace

// DECOMP_FUNC(0x00267fb0, 4672)
void ui_func_00267fb0(UiPartRenderContext* ctx, f32 scale) {
    UiPartSet* parts = ctx->parts;                       // 0x00267FC4
    if (parts->count == 0 || parts->field_10 == 0) {     // 0x00268020..0x00268030
        return;
    }

    // Input colour -> float quad.  The store lands at 0x004EA81C + 0x100,
    // which is exactly 0x004EA91C (`vstmia r0,{s16,s17,s18,s19}`, 0x0026801C).
    f32 tint[4];
    UnpackColor(ctx->color, tint);
    for (s32 i = 0; i < 4; ++i) {
        g_UiPartRenderState.vector[i] = tint[i];
    }

    switch (ctx->kind) {                                 // 0x00268034..0x00268040
    case 0:
    case 3:
    case 8:
        return;
    case 1:
    case 4:
    case 9: {
        // 0x00268070
        s32 visible = 0;
        f32 scale_x = ctx->scale_x * scale;              // 0x00268088
        f32 scale_y = ctx->scale_y * scale;              // 0x0026808C
        u8* resource = *reinterpret_cast<u8**>(
            static_cast<u8*>(ctx->sprite) + 0x0C);   // `ldr fp,[r1,#0xc]`
        UiBufferCursor pos, color, rot, scale_cursor;
        AllocPartCursors(static_cast<u32>(reinterpret_cast<std::uintptr_t>(
                             resource)), pos, color, rot, scale_cursor);

        if ((parts->flags & 1) == 0) {                   // 0x002680D4..0x002680DC
            // Direct screen-space path (0x00268330).
            for (s32 i = 0; i < parts->count; ++i) {
                UiPartEntry& entry = parts->entries[i];
                if (entry.index < 0) {                   // 0x00268348..0x00268350
                    continue;
                }
                f32* p = reinterpret_cast<f32*>(pos.ptr);
                p[0] = entry.vector[0];
                p[1] = entry.vector[1];
                p[2] = entry.vector[2];
                Buffer_Advance(pos);

                *reinterpret_cast<u32*>(color.ptr) = entry.color;
                Buffer_Advance(color);

                entry.rotation = NormalizeAngle(entry.rotation);
                *reinterpret_cast<f32*>(rot.ptr) = entry.rotation;
                Buffer_Advance(rot);

                f32 sx = entry.scale * scale_x;
                f32 sy = entry.scale * scale_y;
                if ((parts->flags & 2) != 0) {           // 0x00268454..0x0026845C
                    sx *= entry.scale_x;
                    sy *= entry.scale_y;
                }
                f32* s = reinterpret_cast<f32*>(scale_cursor.ptr);
                s[0] = sx;
                s[1] = sy;
                Buffer_Advance(scale_cursor);
                ++visible;                               // 0x00268484
            }
            FinishPartDraw(ctx, visible, true);          // 0x00268554
            return;
        }

        // Matrix path (0x002680E0).
        f32 part_vector[4];
        f32 part_matrix[16];
        UiPart_GetVector(parts, part_vector);            // 0x0024faa4
        UiPart_GetMatrix(parts, part_matrix);            // 0x0024fa94
        for (s32 i = 0; i < 4; ++i) {
            g_UiPartRenderState.vector[i] = part_vector[i];
        }
        UiPart_GetSceneMatrix(g_UiPartRenderState.matrix); // 0x002a2f1c
        for (s32 i = 0; i < 4; ++i) {
            g_UiPartRenderState.matrix[12 + i] = part_matrix[i];
        }

        // Save the 16 scene-matrix words (0x0026813C..0x00268188).
        f32 saved_matrix[16];
        std::memcpy(saved_matrix, g_UiPartRenderState.matrix,
                    sizeof(saved_matrix));

        if (parts->count <= 0) {                         // 0x0026818C
            return;
        }

        for (s32 i = 0; i < parts->count; ++i) {
            UiPartEntry& entry = parts->entries[i];
            if (entry.index < 0) {                       // 0x00268190..0x00268198
                continue;
            }
            std::memcpy(g_UiPartRenderState.matrix, saved_matrix,
                        sizeof(saved_matrix));           // 0x002681A8..0x002681D8
            for (s32 j = 0; j < 4; ++j) {
                g_UiPartRenderState.vector[j] = entry.vector[j];
            }

            f32 transformed[4];
            TransformVector(g_UiPartRenderState.matrix,
                            g_UiPartRenderState.vector, transformed);
            for (s32 j = 0; j < 4; ++j) {
                g_UiPartRenderState.vector[j] = transformed[j];
            }

            // Position (3 floats) and colour (a byte-swapped round trip that
            // is exactly the original ARGB word: 0x002682A4..0x002682E4).
            f32* p = reinterpret_cast<f32*>(pos.ptr);
            p[0] = g_UiPartRenderState.vector[0];
            p[1] = g_UiPartRenderState.vector[1];
            p[2] = g_UiPartRenderState.vector[2];
            Buffer_Advance(pos);

            *reinterpret_cast<u32*>(color.ptr) = entry.color;
            Buffer_Advance(color);

            entry.rotation = NormalizeAngle(entry.rotation);
            *reinterpret_cast<f32*>(rot.ptr) = entry.rotation;
            Buffer_Advance(rot);

            f32 sx = entry.scale * scale_x;
            f32 sy = entry.scale * scale_y;
            if ((parts->flags & 2) != 0) {               // 0x00268454
                sx *= entry.scale_x;
                sy *= entry.scale_y;
            }
            f32* s = reinterpret_cast<f32*>(scale_cursor.ptr);
            s[0] = sx;
            s[1] = sy;
            Buffer_Advance(scale_cursor);
            ++visible;                                   // 0x00268484
        }

        FinishPartDraw(ctx, visible, true);              // 0x00268554
        return;
    }

    case 2: {
        // 0x00268610
        u8* sprite = static_cast<u8*>(ctx->sprite);
        u8* resource = *reinterpret_cast<u8**>(sprite + 0x0C); // [sp+0x2c]
        void* texture = ctx->field_44;                  // [sp+0xc]
        s32 visible = 0;
        UiBufferCursor pos, color, rot, scale_cursor, extra_cursor;
        AllocPartCursors(static_cast<u32>(reinterpret_cast<std::uintptr_t>(
                             resource)), pos, color, rot, scale_cursor);
        UiPart_GetBufferAttrib(resource, 0x80, &extra_cursor); // 0x00268670

        void* texture_object = UiPart_SetupTexture(texture, 0); // 0x001e18dc
        *reinterpret_cast<u32*>(resource + 0xB4) =
            static_cast<u32>(reinterpret_cast<std::uintptr_t>(texture_object));
        UiPart_FlushTexture(texture_object);             // 0x00269758

        if ((parts->flags & 1) == 0) {                   // 0x0026869C
            // Direct path (0x00268AB4).
            if (parts->count <= 0) {
                return;
            }
            for (s32 i = 0; i < parts->count; ++i) {
                UiPartEntry& entry = parts->entries[i];
                if (entry.index < 0) {
                    continue;
                }
                f32 params[10] = {};
                UiPart_SetupParams(texture);             // 0x002571c8
                UiPart_GetParams(texture, params);       // 0x00256ffc

                f32* p = reinterpret_cast<f32*>(pos.ptr);
                p[0] = entry.vector[0];
                p[1] = entry.vector[1];
                p[2] = entry.vector[2];
                Buffer_Advance(pos);
                f32* e = reinterpret_cast<f32*>(extra_cursor.ptr);
                e[0] = params[6];
                e[1] = params[7];
                e[2] = params[8];
                e[3] = params[9];
                Buffer_Advance(extra_cursor);

                // Colour quad (0x00268B80..0x00268C2C).
                f32 c[4];
                UnpackColor(entry.color, c);
                for (s32 j = 0; j < 4; ++j) {
                    g_UiPartRenderState.color[j] =
                        c[j] * tint[j];
                }
                *reinterpret_cast<u32*>(color.ptr) =
                    PackColor(g_UiPartRenderState.color);
                Buffer_Advance(color);

                f32 angle = entry.rotation + params[4];  // [sp+0xc0]
                angle = NormalizeAngle(angle);
                *reinterpret_cast<f32*>(rot.ptr) = angle;
                Buffer_Advance(rot);

                f32 sx = entry.scale * scale;            // 0x00268D84
                f32 sy = entry.scale * scale;
                f32* s = reinterpret_cast<f32*>(scale_cursor.ptr);
                s[0] = sx;
                s[1] = sy;
                Buffer_Advance(scale_cursor);
                ++visible;                               // 0x00268D70
            }
            // Tail (0x00268E54) stores the count and colour on the resource.
            if (visible != 0) {
                *reinterpret_cast<u32*>(resource + 0x64) = ctx->color;
                *reinterpret_cast<u32*>(resource + 0x60) =
                    static_cast<u32>(visible);
                u16 id = *reinterpret_cast<u16*>(ctx->parts->handle + 0x54);
                UiPart_PackUV(id);
                UiPart_Submit(static_cast<u32>(
                                  reinterpret_cast<std::uintptr_t>(ctx->sprite)),
                              id);
            }
            return;
        }

        // Matrix path (0x002686A8..0x00268A68).
        f32 part_vector[4];
        f32 part_matrix[16];
        UiPart_GetVector(parts, part_vector);            // 0x0024faa4
        UiPart_GetMatrix(parts, part_matrix);            // 0x0024fa94
        for (s32 i = 0; i < 4; ++i) {
            g_UiPartRenderState.vector[i] = part_vector[i];
        }
        UiPart_GetSceneMatrix(g_UiPartRenderState.matrix); // 0x002a2f1c
        for (s32 i = 0; i < 4; ++i) {
            g_UiPartRenderState.matrix[12 + i] = part_matrix[i];
        }
        f32 saved_matrix[16];
        std::memcpy(saved_matrix, g_UiPartRenderState.matrix,
                    sizeof(saved_matrix));

        if (parts->count <= 0) {
            return;
        }
        for (s32 i = 0; i < parts->count; ++i) {
            UiPartEntry& entry = parts->entries[i];
            if (entry.index < 0) {
                continue;
            }
            std::memcpy(g_UiPartRenderState.matrix, saved_matrix,
                        sizeof(saved_matrix));
            for (s32 j = 0; j < 4; ++j) {
                g_UiPartRenderState.vector[j] = entry.vector[j];
            }
            f32 params[10] = {};
            UiPart_SetupParams(texture);                 // 0x002571c8
            UiPart_GetParams(texture, params);           // 0x00256ffc
            f32 transformed[4];
            TransformVector(g_UiPartRenderState.matrix,
                            g_UiPartRenderState.vector, transformed);
            for (s32 j = 0; j < 4; ++j) {
                g_UiPartRenderState.vector[j] = transformed[j];
            }

            // Position + extra 4 floats (0x00268880..0x002688E8).
            f32* p = reinterpret_cast<f32*>(pos.ptr);
            p[0] = g_UiPartRenderState.vector[0];
            p[1] = g_UiPartRenderState.vector[1];
            p[2] = g_UiPartRenderState.vector[2];
            Buffer_Advance(pos);
            f32* e = reinterpret_cast<f32*>(extra_cursor.ptr);
            e[0] = params[6];
            e[1] = params[7];
            e[2] = params[8];
            e[3] = params[9];
            Buffer_Advance(extra_cursor);

            f32 c[4];
            UnpackColor(entry.color, c);
            for (s32 j = 0; j < 4; ++j) {
                g_UiPartRenderState.color[j] = c[j] * tint[j];
            }
            *reinterpret_cast<u32*>(color.ptr) =
                PackColor(g_UiPartRenderState.color);
            Buffer_Advance(color);

            f32 angle = entry.rotation + params[4];      // [sp+0xc0]
            angle = NormalizeAngle(angle);
            *reinterpret_cast<f32*>(rot.ptr) = angle;
            Buffer_Advance(rot);

            f32 sx = entry.scale * scale;                // 0x00268E1C
            f32 sy = entry.scale * scale;
            f32* s = reinterpret_cast<f32*>(scale_cursor.ptr);
            s[0] = sx;
            s[1] = sy;
            Buffer_Advance(scale_cursor);
            ++visible;                                   // 0x00268DFC
        }
        if (visible == 0) {
            return;
        }
        *reinterpret_cast<u32*>(resource + 0x64) = ctx->color;
        *reinterpret_cast<u32*>(resource + 0x60) = static_cast<u32>(visible);
        u16 id = *reinterpret_cast<u16*>(ctx->parts->handle + 0x54);
        UiPart_PackUV(id);
        UiPart_Submit(static_cast<u32>(
                          reinterpret_cast<std::uintptr_t>(ctx->sprite)), id);
        return;
    }

    case 5: {
        // 0x00268EEC: blit each part through the +0x34 handle array.
        u32* handles = ctx->handles_34;
        for (s32 i = 0; i < parts->count; ++i) {
            UiPartEntry& entry = parts->entries[i];
            if (entry.index < 0) {                       // 0x00268F08..0x00268F10
                continue;
            }
            f32 c[4];
            UnpackColor(entry.color, c);                 // 0x00268F14..0x00268F74
            for (s32 j = 0; j < 4; ++j) {
                g_UiPartRenderState.vector[j] = c[j];
                g_UiPartRenderState.color[j] = tint[j];
            }
            for (s32 j = 0; j < 4; ++j) {
                g_UiPartRenderState.vector[j] *=
                    g_UiPartRenderState.color[j];        // 0x00268F88..0x00268FC4
            }
            u32 packed = PackColor(g_UiPartRenderState.vector);
            UiPart_SubmitA(handles[i], packed);          // 0x001e1900
            UiPart_SubmitB(handles[i]);                  // 0x0024c564
        }
        return;
    }

    case 6: {
        // 0x00269050: same loop through the +0x3C handle array.
        u32* handles = ctx->handles_3c;
        for (s32 i = 0; i < parts->count; ++i) {
            UiPartEntry& entry = parts->entries[i];
            if (entry.index < 0) {
                continue;
            }
            f32 c[4];
            UnpackColor(entry.color, c);
            for (s32 j = 0; j < 4; ++j) {
                g_UiPartRenderState.color[j] = c[j];
            }
            for (s32 j = 0; j < 4; ++j) {
                g_UiPartRenderState.color[j] *= tint[j];
            }
            u32 packed = PackColor(g_UiPartRenderState.color);
            UiPart_SubmitC(handles[i], packed);          // 0x002a37dc
            UiPart_SubmitD(handles[i]);                  // 0x00281adc
        }
        return;
    }

    case 7: {
        // 0x002691BC: direct model draw.
        u16 id = *reinterpret_cast<u16*>(parts->handle + 0x54);
        UiPart_PackUV(id);                               // 0x0025741c
        UiPart_DrawDirect(ctx);                          // 0x002c7cc4
        return;
    }

    default:
        return;
    }
}

// ---------------------------------------------------------------------------
// 0x00197D2C: quest list / detail screen
// ---------------------------------------------------------------------------

namespace {

/** Quest row fields read by 0x00197D2C. */
struct QuestRuntimeRow {
    u8  pad_000[0x150];
    u32 objective_count;            // +0x150: `ldr r1,[r7,#0x150]` (0x00197FD8)
    u16 primary_state;              // +0x154: `ldrh r0,[r5]` (0x00198140)
    u16 primary_target;             // +0x156: `ldrh r0,[r5,#2]` (0x00198200)
    u16 primary_reward;             // +0x158: `ldrh r1,[r5,#4]` (0x001982F8)
};
static_assert(offsetof(QuestRuntimeRow, objective_count) == 0x150);
static_assert(offsetof(QuestRuntimeRow, primary_state) == 0x154);
static_assert(offsetof(QuestRuntimeRow, primary_target) == 0x156);
static_assert(offsetof(QuestRuntimeRow, primary_reward) == 0x158);

/** 0x20-byte reward entry returned by 0x002990DC. */
struct QuestRewardEntry {
    u16 field_00;
    u16 field_02;
    u16 item_id;                    // +0x04: `ldrh r0,[sp,#0xc]` (0x00198A20)
    u16 field_06;
    u8  has_name;                   // +0x08? see has_name_offset below
    u8  pad_09[0x17];
};
static_assert(offsetof(QuestRewardEntry, item_id) == 0x04);

constexpr const char* kQuestSeparator = "\x81\x7C \x81\x7C \x81\x7C";
constexpr const char* kQuestDash      = "\x81\x7C\x81\x7C\x81\x7C";
constexpr const char* kQuestNoData    = "\x83\x66\x81\x5B\x83\x5E\x96\xB3\x82\xB5x%d";
constexpr const char* kQuestMacca     = "%s\x81\x40\x82\x6D\x82\x8F\x82\x8E\x82\x85";
constexpr const char* kQuestRewardFmt = "%s\x81\x40%s\x81\x5F%s";

} // namespace

// DECOMP_FUNC(0x00197d2c, 4432)
void ui_func_00197d2c() {
    QuestUiView* work = reinterpret_cast<QuestUiView*>(script::g_UIQuestWork);

    // 0x00197D38..0x00197DA8: base offsets from the first quest panel.
    const s32 x0 = UiAnimSprite_GetPosX(&work->sprite_034);
    const s32 y0 = UiAnimSprite_GetPosY(&work->sprite_034);
    (void)UiGpu_TransformCoord(g_AsdGpuState, 0.325f);   // 0x00197D50 (result discarded)

    UiListCursor* cursor = work->field_5c4 ? &work->cursor_5fc
                                           : &work->cursor_660;
    u8* rows = work->field_5c4 ? work->rows_6c4
                               : reinterpret_cast<u8*>(work) + 0x78A;
    const s32 selected = UiListCursor_GetSelectedRow(cursor);
    const s32 scroll = UiListCursor_GetScrollOffset(cursor);
    u16 quest_id = *reinterpret_cast<u16*>(
        rows + (scroll + selected) * 2);                    // 0x00197DAC..0x00197DBC
    if (work->field_5f2 != 0) {                             // 0x00197DC0..0x00197DD4
        quest_id = work->field_97e;
    }

    // 0x00197DD8..0x00197E2C: three top panels.
    const s32 panel_y_offset = static_cast<s32>(
        UiGpu_TransformCoord(g_AsdGpuState, 0.32f));        // 0x3EA3D70A
    s32 anchor_x = x0;
    s32 anchor_y = y0;
    const u32 screen_state = *reinterpret_cast<const u32*>(
        reinterpret_cast<const u8*>(work) + 0x04);
    if (screen_state == 0x17 || screen_state == 0x18 ||
        screen_state == 0x19) {                             // 0x00197DF8..0x00197E08
        anchor_x += UiAnimSprite_GetPosX(&work->sprite_494);
        anchor_y += UiAnimSprite_GetPosY(&work->sprite_494);
    }
    UiSprite_DrawPanel(2, 0x29, 2, anchor_x + panel_y_offset,
                       anchor_y, 0x65);                     // 0x00197E44
    UiSprite_DrawPanel(2, 0x29, 1, x0 + static_cast<s32>(
        UiGpu_TransformCoord(g_AsdGpuState, 0.315f)), y0, 0x65); // 0x3EA147AE
    UiSprite_DrawPanel(2, 0x29, 0, x0 + static_cast<s32>(
        UiGpu_TransformCoord(g_AsdGpuState, 0.31f)), y0, 0x65);  // 0x3E9EB852

    if (quest_id == 0) {
        // 0x001984B8..0x0019853C: empty quest list.
        const s32 empty_offset = static_cast<s32>(
            UiGpu_TransformCoord(g_AsdGpuState, 0.325f));
        const s32 empty_x = x0 + UiAnimSprite_GetPosX(&work->sprite_1d8) +
                            empty_offset;
        const s32 empty_y = y0 + UiAnimSprite_GetPosY(&work->sprite_1d8);
        UiSprite_DrawPanel(2, 0x29, 3, empty_x, empty_y, 0x65);
        return;
    }

    QuestRuntimeRow* row = static_cast<QuestRuntimeRow*>(
        Quest_GetRow(quest_id));                            // 0x00197EC0
    const s32 detail_offset = static_cast<s32>(
        UiGpu_TransformCoord(g_AsdGpuState, 0.31f));        // 0x00197ED0

    // 0x00197EE4..0x00197F28: new/old quest marker.
    if (Quest_IsNew(quest_id)) {
        UiSprite_DrawNode(2, 0x29, 0x10, x0 + detail_offset, y0, 0x68);
    } else {
        UiSprite_DrawNode(2, 0x29, 0x0F, x0 + detail_offset, y0, 0x68);
    }

    const Npc2dLayoutNode* node = UiLayout_GetNode(0x29, 0x11); // 0x00197F2C
    Quest_DrawIcon(quest_id, x0 + detail_offset + node->x,
                   y0 + node->y, 0x6A);                     // 0x00197F54

    node = UiLayout_GetNode(0x29, 0x12);                    // 0x00197F58
    char text[0x100];
    UiFont_FormatString(text, "%s", Quest_GetTitle(quest_id)); // 0x00197F70
    UiFont_DrawText(3, 0xFFFFFFFFu, text,
                    static_cast<f32>(x0 + detail_offset + node->x),
                    static_cast<f32>(y0 + node->y),
                    1.8f, 0.0f, 1.0f);                      // 0x3EE66666

    // 0x00197FC4..0x00198040: objective bullet column.
    const s32 objective_offset = static_cast<s32>(
        UiGpu_TransformCoord(g_AsdGpuState, 0.305f));       // 0x3E9C28F6
    for (u32 i = 0; i < row->objective_count; ++i) {
        const Npc2dLayoutNode* marker =
            UiLayout_GetNode(0x29, 5 + (i / 2));            // 0x00197FF8
        const s32 mx = x0 + objective_offset + marker->x;
        const s32 my = y0 + marker->y;
        if ((i & 1) != 0) {
            UiSprite_DrawNode(2, 0x29, 0x0E, mx, my, 0x6A); // 0x00198024
        } else {
            UiSprite_DrawNode(2, 0x29, 0x0D, mx, my, 0x6A); // 0x001981E4
        }
    }

    const s32 desc_offset = static_cast<s32>(
        UiGpu_TransformCoord(g_AsdGpuState, 0.315f));       // 0x00198048
    node = UiLayout_GetNode(0x29, 0x1A);                    // 0x00198058
    UiFont_FormatString(text, "%s", Quest_GetDescription(quest_id));
    UiFont_DrawText(2, 0xFFu, text,
                    static_cast<f32>(x0 + desc_offset + node->x),
                    static_cast<f32>(y0 + node->y),
                    1.8f, 0.0f, 1.0f);                      // 0x3EE66666

    const u8* flag_table = Quest_GetFlagTable();            // 0x001980CC
    const u8 quest_flags = flag_table[0x200 + quest_id * 4];
    u16* state_ptr = reinterpret_cast<u16*>(
        reinterpret_cast<u8*>(row) + 0x154 +
        (((quest_flags >> 3) & 1) * 3) * 4);                // 0x0019811C..0x0019812C
    if ((quest_flags & 8) != 0 && *state_ptr == 0) {        // 0x00198130..0x0019813C
        state_ptr = reinterpret_cast<u16*>(
            reinterpret_cast<u8*>(row) + 0x154);
    }

    switch (*state_ptr) {                                   // 0x00198140..0x00198158
    case 1: {
        if (row->primary_target != 0) {                     // 0x00198204
            node = UiLayout_GetNode(0x29, 0x1B);
            Quest_DrawObjectiveIcon(row->primary_target,
                                    x0 + desc_offset + node->x,
                                    y0 + node->y, 0x6A);    // 0x00198238
            node = UiLayout_GetNode(0x29, 0x1C);
            UiFont_FormatString(text, "%s",
                                Quest_GetObjectiveName(row->primary_target));
            UiFont_DrawText(2, 0xFFFFFFFFu, text,
                            static_cast<f32>(x0 + desc_offset + node->x),
                            static_cast<f32>(y0 + node->y),
                            1.8f, 0.0f, 1.0f);              // 0x3EE66666
            const f32 width = Quest_MeasureText(text, 2);   // 0x001982B0
            const s32 extra = static_cast<s32>(width + 3.0f); // 0x40400000
            node = UiLayout_GetNode(0x29, 0x1B);
            UiFont_DrawFormatted(0,
                                 x0 + desc_offset + node->x + extra,
                                 y0 + node->y, 0, 7, 0x6A, "*", 0); // 0x001982F4
            char reward[0x80];
            Quest_FormatReward(reward, row->primary_reward); // 0x00198300
            UiFont_DrawText(2, 0xFFFFFFFFu, reward,
                            static_cast<f32>(x0 + desc_offset + node->x +
                                             extra + 7),
                            static_cast<f32>(y0 + node->y),
                            1.8f, 0.0f, 1.0f);              // 0x3EE66666
        } else {
            UiFont_FormatString(text, kQuestNoData, row->primary_reward); // 0x0019836C
        }
        break;
    }
    case 3: {
        char reward[0x80];
        Quest_FormatReward(reward, row->primary_reward);    // 0x00198384
        UiFont_FormatString(text, kQuestMacca, reward);     // 0x00198394
        break;
    }
    case 4: {
        UiFont_FormatString(text, "%s",
                            Quest_GetRewardItemName(row->primary_target)); // 0x001983B4
        break;
    }
    default: {
        UiFont_FormatString(text, kQuestDash);              // 0x0019815C
        break;
    }
    }

    // 0x00198168..0x001981AC: state text at node 0x1B.
    node = UiLayout_GetNode(0x29, 0x1B);
    UiFont_DrawText(2, 0xFFFFFFFFu, text,
                    static_cast<f32>(x0 + desc_offset + node->x),
                    static_cast<f32>(y0 + node->y),
                    1.8f, 0.0f, 1.0f);                      // 0x3EE66666

    // 0x001981B0..0x00198438: main quest panel.
    const s32 preview_offset = static_cast<s32>(
        UiGpu_TransformCoord(g_AsdGpuState, 0.325f));
    s32 panel_x = x0 + preview_offset;
    s32 panel_y = y0;
    if (screen_state == 0x17 || screen_state == 0x18 ||
        screen_state == 0x19) {                             // 0x001983E0
        panel_x = x0 + preview_offset +
                  UiAnimSprite_GetPosX(&work->sprite_494);
        panel_y = y0 + UiAnimSprite_GetPosY(&work->sprite_494);
        if (screen_state == 0x18) {                         // 0x00198404
            goto draw_quest_preview;
        }
    }
    if (*reinterpret_cast<const u32*>(
            reinterpret_cast<const u8*>(work) + 0x08) == 0x18) {
        goto draw_quest_preview;                            // 0x00198410
    }

    UiSprite_DrawNode(2, 0x29, 0x23, panel_x, panel_y, 0x6A); // 0x00198438
    node = UiLayout_GetNode(0x29, 0x25);                    // 0x00198444
    UiAnimSprite_DrawAt(work->handle_5d8,
                        panel_x + node->x, panel_y + node->y,
                        0x6F, 6, 0, 1.0f);                  // 0x0019847C
    node = UiLayout_GetNode(0x29, 0x26);                    // 0x00198480
    UiAnimSprite_DrawAt(work->handle_5d8,
                        panel_x + node->x, panel_y + node->y,
                        0x6F, 6, 1, 1.0f);                  // 0x001984B4
    goto after_quest_preview;

draw_quest_preview:
    // 0x0019857C..0x00198678: 3D preview with two render-mode overrides.
    UiSprite_SetGlobalAlpha(*reinterpret_cast<const f32*>(
        reinterpret_cast<const u8*>(work) + 0x520 + 0x20)); // 0x00198580
    GpuModeSlotSet(static_cast<u32>(reinterpret_cast<std::uintptr_t>(
        UiGpu_SetRenderMode(6, 1, 0))));                    // 0x002c5fa4
    UiSprite_DrawNode(2, 0x29, 0x60, panel_x, panel_y, 0x68); // 0x001985F8
    GpuModeSlotSet(static_cast<u32>(reinterpret_cast<std::uintptr_t>(
        UiGpu_SetRenderMode(6, 1, 0))));
    UiSprite_SetGlobalAlpha(1.0f);                           // 0x0019864C
    UiSprite_DrawNode(2, 0x29, 0x24, panel_x, panel_y, 0x6A); // 0x0019866C

after_quest_preview:
    // 0x0019867C..0x00198784: quest availability / tracking flags.
    if ((*reinterpret_cast<const u8*>(reinterpret_cast<const u8*>(row) + 6) != 0 &&
         Quest_IsRewardKnown(quest_id))) {
        if (Quest_GetTrackedId() == quest_id) {             // 0x001986D0
            if (screen_state == 0x0C) {                     // 0x001986E4
                Quest_DrawRewardRow(reinterpret_cast<u8*>(work) + 0x264,
                                    static_cast<f32>(preview_offset)); // 0x00198728
            } else {
                UiSprite_DrawNode(2, 0x29, 0x2A, panel_x, panel_y, 0x68);
            }
        } else if (Quest_IsNew(quest_id)) {                 // 0x00198738
            UiSprite_DrawNode(2, 0x29, 0x2B, panel_x, panel_y, 0x68); // 0x00198780
        }
    } else if (Quest_IsNew(quest_id)) {                     // 0x001986A4 / 0x00198750
        UiSprite_DrawNode(2, 0x29, 0x2B, panel_x, panel_y, 0x68);
    }

    // 0x00198784..0x001989A0: reward rows.
    if (work->field_5d0 > 0) {
        const s32 base_x = x0 + preview_offset;
        for (s32 i = 0; i < work->field_5d0; ++i) {
            if (work->field_5c8 == i) {                     // 0x0019879C
                continue;
            }
            node = UiLayout_GetNode(0x29, 0x48 + i);        // 0x001987A8
            UiSprite_DrawNode(2, 0x29, 0x40, base_x + node->x,
                              y0 + node->y, 0x65);          // 0x001987E0
            if (i == 0) {
                UiSprite_DrawNode(2, 0x29, 0x41, base_x + node->x,
                                  y0 + node->y, 0x6A);      // 0x00198850
            } else if (i == 1 &&
                       (*reinterpret_cast<const u8*>(
                            reinterpret_cast<const u8*>(row) + 7) & 0x40) != 0) {
                UiSprite_DrawNode(2, 0x29, 0x42, base_x + node->x,
                                  y0 + node->y, 0x6A);      // 0x00198894
            } else if (i != 1) {
                UiSprite_DrawNode(2, 0x29, 0x43, base_x + node->x,
                                  y0 + node->y, 0x6A);      // 0x001988CC
            }
        }
    }

    if (work->field_5c8 == 0) {                             // 0x00198810
        node = UiLayout_GetNode(0x29, 0x34);                // 0x001988E4
        const s32 list_x = x0 + preview_offset + node->x;
        const s32 list_y = y0 + node->y;
        for (s32 i = 0; i < 7; ++i) {
            UiAnimSprite_DrawAt(work->handle_5d4,
                                list_x, list_y + i * 0x11,
                                0x6F, 6, i, 1.0f);          // 0x00198914
        }
        const s32 bottom_offset = static_cast<s32>(
            UiGpu_TransformCoord(g_AsdGpuState, 0.315f));   // 0x00198928
        node = UiLayout_GetNode(0x29, 0x48);                // 0x00198944
        const s32 bx = x0 + bottom_offset + node->x;
        const s32 by = y0 + node->y;
        UiSprite_DrawNode(2, 0x29, 0x44, bx, by, 0x6F);     // 0x00198974
        UiSprite_DrawNode(2, 0x29, 0x45, bx, by, 0x74);     // 0x0019899C
    } else if (work->field_5c8 == 1 &&
               (*reinterpret_cast<const u8*>(
                    reinterpret_cast<const u8*>(row) + 7) & 0x40) != 0) {
        // 0x001989B8..0x00198C18: six reward detail rows.
        s32 drawn_rows = 0;
        for (s32 i = 0; i < 6; ++i) {
            QuestRewardEntry reward{};
            if (Quest_GetRewardEntry(quest_id, i, &reward)) { // 0x001989D8
                node = UiLayout_GetNode(0x29, 0x34);        // 0x001989F0
                char line[0x80];
                char value[0x80];
                const u16 line_id = *reinterpret_cast<const u16*>(
                    reinterpret_cast<const u8*>(row) + 0x170 + i * 8);
                Quest_FormatReward(line, line_id);          // 0x00198A14
                Quest_FormatReward(value, reward.item_id);  // 0x00198A28
                UiFont_FormatString(
                    text, kQuestRewardFmt, line,
                    (*reinterpret_cast<const u8*>(
                         reinterpret_cast<const u8*>(&reward) + 6) != 0)
                        ? Quest_GetRewardItemName(reward.item_id)
                        : Item_GetShortNameString(reward.item_id),
                    value);                             // 0x00198A48
                UiFont_DrawText(3, 0x320202FFu, text,
                                static_cast<f32>(x0 + preview_offset +
                                                 node->x + i * 0x11),
                                static_cast<f32>(y0 + node->y),
                                0.58f, 0.0f, 1.0f);     // 0x3F147AE1
                ++drawn_rows;
            }
        }
        // 0x00198AEC..0x00198C18: additional requirement line.  The flag at
        // sp+0x138 starts set and is cleared by the IsNew/IsExpired pair.
        bool extra_line = true;
        if (*reinterpret_cast<const u8*>(reinterpret_cast<const u8*>(row) + 6) == 0 &&
            Quest_IsNew(quest_id) && !Quest_IsExpired(quest_id)) {
            extra_line = false;
        }
        if (extra_line &&
            *reinterpret_cast<const u8*>(reinterpret_cast<const u8*>(row) + 6) == 0 &&
            Quest_IsCompleted(quest_id) && !Quest_IsExpired(quest_id)) {
            node = UiLayout_GetNode(0x29, 0x34);            // 0x00198B40
            UiFont_DrawText(3, 0x320202FFu, text,
                            static_cast<f32>(x0 + preview_offset + node->x +
                                             drawn_rows * 0x11 + 0x11),
                            static_cast<f32>(y0 + node->y),
                            0.58f, 0.0f, 1.0f);         // 0x00198C14
        }
        // 0x00198B20..0x00198C14: one TBB row rendered below the reward
        // list.  The row index is 7 for value 1, 8 otherwise and 9 when the
        // quest is flagged new or +0x19C is zero (0x00198B58..0x00198CCC).
        if (*reinterpret_cast<const u8*>(reinterpret_cast<const u8*>(row) + 6) == 0 &&
            extra_line) {
            s32 row_index;
            if (Quest_IsCompleted(quest_id)) {
                row_index = 9;
            } else {
                const u16 selector = *reinterpret_cast<const u16*>(
                    reinterpret_cast<const u8*>(row) + 0x19C);
                if (selector == 0) {
                    row_index = 9;
                } else {
                    row_index = (selector == 1) ? 7 : 8;
                }
            }
            void* sub_table = Tbb_GetGlobalSubTable(0x34, 0); // 0x00198B80
            void* payload = Tbb_GetPayloadData(sub_table);    // 0x00198B8C
            if (static_cast<u32>(row_index) < Tbb_GetRowCount(sub_table)) {
                const u8* entry = reinterpret_cast<const u8*>(payload) +
                                  static_cast<u32>(row_index) * 0x4A;
                if (entry + 1 != nullptr) {
                    node = UiLayout_GetNode(0x29, 0x34);      // 0x00198B3C
                    UiFont_FormatString(text, "%s",
                                        reinterpret_cast<const char*>(entry + 1));
                    UiFont_DrawText(3, 0x320202FFu, text,
                                    static_cast<f32>(x0 + preview_offset +
                                                     node->x +
                                                     drawn_rows * 0x11 + 0x11),
                                    static_cast<f32>(y0 + node->y),
                                    0.58f, 0.0f, 1.0f);       // 0x00198C14
                }
            }
        }

        // 0x00198C18..0x00198C98: two hint panels.
        node = UiLayout_GetNode(0x29, 0x49);                // 0x00198C38
        UiSprite_DrawNode(2, 0x29, 0x44,
                          x0 + preview_offset + node->x,
                          y0 + node->y, 0x6F);              // 0x00198C6C
        UiSprite_DrawNode(2, 0x29, 0x46,
                          x0 + preview_offset + node->x,
                          y0 + node->y, 0x74);              // 0x00198C98
    } else if (work->field_5c8 == 2 ||
               (work->field_5c8 == 1 &&
                (*reinterpret_cast<const u8*>(
                     reinterpret_cast<const u8*>(row) + 7) & 0x40) == 0)) {
        // 0x00198CDC..0x00198D28: second seven-line list.
        node = UiLayout_GetNode(0x29, 0x34);                // 0x00198CEC
        const s32 list_x = x0 + preview_offset + node->x;
        const s32 list_y = y0 + node->y;
        for (s32 i = 0; i < 7; ++i) {
            UiAnimSprite_DrawAt(work->handle_5dc,
                                list_x, list_y + i * 0x11,
                                0x6F, 6, i, 1.0f);          // 0x00198D1C
        }
        if (work->field_5c8 == 2) {                         // 0x00198D40
            node = UiLayout_GetNode(0x29, 0x4A);            // 0x00198E44
        } else {
            node = UiLayout_GetNode(0x29, 0x49);
            UiSprite_DrawNode(2, 0x29, 0x44,
                              x0 + preview_offset + node->x,
                              y0 + node->y, 0x6F);          // 0x00198D8C
            UiSprite_DrawNode(2, 0x29, 0x47,
                              x0 + preview_offset + node->x,
                              y0 + node->y, 0x74);          // 0x00198DB8
        }
    }

    // 0x00198DBC..0x00198E2C: bottom two panels.
    if (work->field_5d0 > 1) {
        const s32 bottom_offset = static_cast<s32>(
            UiGpu_TransformCoord(g_AsdGpuState, 0.32f));
        s32 left = 4;
        s32 right = 5;
        if (screen_state == 5 || screen_state == 4) {       // 0x00198DE8
            const s16 mode = *reinterpret_cast<const s16*>(
                reinterpret_cast<const u8*>(work) + 0x1D8 + 0x50);
            if (mode == 3 || mode == 1) {
                left = 6;
            } else if (mode == 2 || mode == 0) {
                right = 7;
            }
        }
        const s32 bx = x0 + bottom_offset;
        UiSprite_DrawPanel(2, 0x29, left, bx, y0, 0x79);    // 0x00198E14
        UiSprite_DrawPanel(2, 0x29, right, bx, y0, 0x79);   // 0x00198E2C
    }
}

// ---------------------------------------------------------------------------
// 0x001F0454: camp fusion inheritance screen
// ---------------------------------------------------------------------------

namespace {

constexpr const char* kFusionTitleA =
    "\x82\x68\x82\x8E\x82\x88\x82\x85\x82\x92\x82\x89\x82\x94\x82\x89\x82\x8E\x82\x87";
constexpr const char* kFusionTitleB =
    "\x82\x6F\x82\x81\x82\x92\x82\x85\x82\x8E\x82\x94\x81\x40\x82\x72\x82\x8B"
    "\x82\x89\x82\x8C\x82\x8C\x82\x93";
constexpr const char* kFusionMoney =
    "\x82\x6D\x82\x8F\x82\x8E\x82\x85";
constexpr const char* kFusionDash = "\x81\x7C \x81\x7C \x81\x7C";

/** 0x001F0454 uses the workspace-relative pair scan produced by
 *  0x0026AC34 into eight u16 slots at sp+0x680. */
struct FusionPairBuffer {
    u16 values[8];
};

} // namespace

// DECOMP_FUNC(0x001f0454, 5764)
void ui_func_001f0454(s32 x, s32 y, s32 mode, s32 flag, s32 has_target,
                      s32 slide_dir) {
    CampFusionView* work = static_cast<CampFusionView*>(Camp_GetMainWork());
    if (work == nullptr) {                                  // 0x001F0468
        return;
    }

    const s32 slide_offset = (work->field_3fc / 4) % 3;     // 0x001F062C..0x001F0658
    f32 fade = 1.0f;                                        // s17 = s16 (0x001F09AC)
    bool fade_latched = false;                              // [sp+0x690]

    // 0x001F046C..0x001F0568: fixed frame panels.
    UiSprite_DrawPanel(2, 0x24, 1, x, y, 0x65);
    UiSprite_DrawNode(2, 0x24, 0x163, x, y, 0x6A);
    UiSprite_DrawNode(2, 0x24, 0x164, x, y, 0x6A);
    UiSprite_DrawNode(2, 0x24, 0x165, x, y, 0x6F);
    UiSprite_DrawNode(2, 0x24, 0x166, x, y, 0x6A);
    UiSprite_DrawNode(2, 0x24, 0x167, x, y, 0x6F);
    UiSprite_DrawNode(2, 0x24, 0x168, x, y, 0x6A);
    UiSprite_DrawNode(2, 0x24, 0x16B, x, y, 0x6F);
    UiSprite_DrawNode(2, 0x24, 0x16C, x, y, 0x74);

    // 0x001F056C..0x001F0628: "INHERITING" / "Parent Skills".
    char text[0x100];
    const Npc2dLayoutNode* node = UiLayout_GetNode(0x24, 0x168);
    UiFont_FormatString(text, "%s", kFusionTitleA);
    UiFont_DrawText(3, 0xFFu, text,
                    static_cast<f32>(x + node->x),
                    static_cast<f32>(y + node->y),
                    0.0f, 0.0f, 1.0f);
    node = UiLayout_GetNode(0x24, 0x169);
    UiFont_FormatString(text, "%s", kFusionTitleB);
    UiFont_DrawText(3, 0xFFu, text,
                    static_cast<f32>(x + node->x),
                    static_cast<f32>(y + node->y),
                    0.0f, 0.0f, 1.0f);

    // 0x001F062C..0x001F06C8: two sliding bars and the alpha-blended frame.
    UiSprite_DrawNode(2, 0x24, 0x16D, x - slide_offset, y, 0x6F);
    UiSprite_SetGlobalAlpha(*reinterpret_cast<const f32*>(
        reinterpret_cast<const u8*>(work) + 0x24 + 0x20));  // 0x001F066C
    UiSprite_DrawNode(2, 0x24, 0x16E, x - slide_offset, y, 0x6A);
    UiSprite_SetGlobalAlpha(1.0f);
    UiSprite_DrawNode(2, 0x24, 0x4F, x, y, 0x6A);

    // 0x001F06CC..0x001F0748: resolve the row used by the whole screen.
    u8* row = nullptr;
    if (flag != 0) {
        row = static_cast<u8*>(Battle_GetTalkEntry(work->field_5210));
    } else if (slide_dir != 0) {
        const u32 packed = *reinterpret_cast<const u32*>(
            work->records_1390 + 4);
        row = static_cast<u8*>(Battle_GetTalkEntry(packed >> 2));
    } else {
        const u16 index = work->field_6ce2;
        const u8* record = work->records_1390 + index * 8;
        const u32 packed = *reinterpret_cast<const u32*>(record + 4);
        row = static_cast<u8*>(Battle_GetTalkEntry(packed >> 2));
    }

    // 0x001F074C..0x001F0828: result name, description and header count.
    node = UiLayout_GetNode(0x24, 0x4D);
    UiFont_FormatString(text, "%s",
                        Item_GetShortNameString(*reinterpret_cast<u16*>(row)));
    UiFont_DrawText(2, 0xFFFFFFFFu, text,
                    static_cast<f32>(x + node->x),
                    static_cast<f32>(y + node->y),
                    0.0f, 0.0f, 1.0f);
    node = UiLayout_GetNode(0x24, 0x4E);
    UiFont_FormatString(text, "%s",
                        Item_GetDescriptionString(*reinterpret_cast<u16*>(row)));
    UiFont_DrawText(2, 0xF49800FFu, text,
                    static_cast<f32>(x + node->x),
                    static_cast<f32>(y + node->y),
                    0.0f, 0.0f, 1.0f);
    node = UiLayout_GetNode(0x24, 0x51);

    // 0x001F0888..0x001F08B8: inherited-skill count.
    UiFont_DrawFormatted(0, x + node->x, y + node->y,
                         1, 2, 0x8D, "%d", row[3]);

    // 0x001F08BC..0x001F0908: leading non-zero party-slot count.
    const void* party_list = work->list_91a0;
    s32 active = 0;
    while (UiList_CountActiveRows(party_list) > 0 &&
           work->rows_9010[active] != 0) {
        ++active;
        if (UiList_CountActiveRows(party_list) <= active) {
            break;
        }
    }

    // 0x001F0908..0x001F0988: item icon, description icon and local cursor.
    node = UiLayout_GetNode(0x24, 0x1ED);
    UiSkill_DrawItemIconAndCount(*reinterpret_cast<u16*>(row),
                                 x + node->x, y + node->y, 0x8D, 0);
    Item_DrawDescriptionIcon(*reinterpret_cast<u16*>(row),
                             x + node->x, y + node->y, 0x92);

    alignas(8) u8 local_cursor_storage[0x604]{};
    UiListCursor* local_cursor =
        reinterpret_cast<UiListCursor*>(local_cursor_storage);
    UiListCursor_InitFromRow(*reinterpret_cast<u16*>(row), local_cursor);
    const s32 slot_count = UiListCursor_CountPartySlots(local_cursor);
    UiListCursor* cursor = &work->cursor_9204;

    // 0x001F09AC..0x001F10E0: eight list rows.
    s32 row_x = x;
    s32 row_y = y;
    for (s32 i = 0; i < 8; ++i) {
        node = UiLayout_GetNode(0x24, 0x17D + i);
        if (i >= slot_count) {
            UiSprite_DrawNode(2, 0x24, 0x229, row_x + node->x, row_y + node->y, 0x65);
            UiSprite_DrawNode(2, 0x24, 0x16F, row_x + node->x, row_y + node->y, 0x65);
            UiSprite_DrawNode(2, 0x24, 0x170, row_x + node->x, row_y + node->y, 0x65);
            continue;
        }

        if (i < active - work->count_926c) {                // 0x001F0A54..0x001F0A64
            UiSprite_DrawNode(2, 0x24, 0x172, row_x + node->x, row_y + node->y, 0x65);
        } else if (UiListCursor_GetRowCount(cursor) > work->count_926c &&
                   i == active) {                           // 0x001F0AA0..0x001F0ABC
            if (mode == 1) {                                // 0x001F0AC0
                if (work->field_3fc < 1) {
                    fade = static_cast<f32>(1 - work->field_3fc);
                    UiSprite_SetGlobalAlpha(fade);
                }
            } else if (mode == 2 || mode == 3) {
                if (fade_latched) {
                    row_y += work->field_3fc * -3;              // 0x001F0B40..0x001F0B48
                }
            }
            UiSprite_DrawNode(2, 0x24, 0x173, row_x + node->x, row_y + node->y, 0x65);
        } else {
            if (mode == 1) {                                // 0x001F0B88
                if (work->field_3fc >= 1) {
                    const s32 sel = UiListCursor_GetSelectedRow(cursor) +
                                    UiListCursor_GetScrollOffset(cursor);
                    if (work->rows_9010[i] == work->rows_9020[sel]) {
                        row_x += UiAnimSprite_GetPosX(&work->sprite_2e0);
                        row_y += UiAnimSprite_GetPosY(&work->sprite_2e0);
                        fade = *reinterpret_cast<const f32*>(
                            reinterpret_cast<const u8*>(work) + 0x2E0 + 0x20);
                        UiSprite_SetGlobalAlpha(fade);
                    }
                }
            } else if (mode == 2) {                         // 0x001F0C04
                if (work->field_3fc <= 5) {
                    if (fade_latched) {
                        row_y += work->field_3fc * -3;          // 0x001F0C34..0x001F0C3C
                    }
                    const s32 sel = UiListCursor_GetSelectedRow(cursor) +
                                    UiListCursor_GetScrollOffset(cursor);
                    if (work->rows_9010[i] == work->rows_9020[sel]) {
                        fade = static_cast<f32>(5 - work->field_3fc) * 0.2f;
                        UiSprite_SetGlobalAlpha(fade);
                        fade_latched = true;
                    }
                }
            } else if (mode == 3) {                         // 0x001F0C88
                if (work->field_3fc <= 5) {
                    if (fade_latched) {
                        row_y += work->field_3fc * -3;
                    }
                    s32 last = 7;
                    while (last > -1) {                     // 0x001F0CA4..0x001F0CD8
                        if (work->rows_9010[last] != 0) {
                            break;
                        }
                        if (work->rows_9010[last - 1] != 0) {
                            --last;
                            break;
                        } else {
                            last -= 2;
                            if (last <= -1) {
                                break;
                            }
                        }
                    }
                    if (i == last) {
                        fade = static_cast<f32>(5 - work->field_3fc) * 0.2f;
                        UiSprite_SetGlobalAlpha(fade);
                        fade_latched = true;
                    }
                }
            }
            UiSprite_DrawNode(2, 0x24, 0x171, row_x + node->x, row_y + node->y, 0x65);
        }

        UiSprite_DrawNode(2, 0x24, 0x16F, row_x + node->x, row_y + node->y, 0x65);
        UiSprite_DrawNode(2, 0x24, 0x170, row_x + node->x, row_y + node->y, 0x65);

        if (work->rows_9010[i] != 0) {
            // 0x001F0D7C..0x001F0F30
            UiSprite_DrawNode(2, 0x24, 0x174, row_x + node->x, row_y + node->y, 0x6A);
            UiSprite_DrawNode(2, 0x24, 0x175, row_x + node->x, row_y + node->y, 0x6A);
            UiSprite_DrawNode(2, 0x24, 0x176, row_x + node->x, row_y + node->y, 0x6F);

            const u32 color = (active - work->count_926c > i) ? 0xFFFFFFFFu
                                                               : 0xFFu; // 0x001F0E1C..0x001F0E20
            UiFont_FormatString(text, "%s",
                                Item_GetNameString(work->rows_9010[i]));
            const Npc2dLayoutNode* name_node =
                UiLayout_GetNode(0x24, 0x178);              // 0x001F0E38
            UiFont_DrawText(2, color, text,
                            static_cast<f32>(row_x + node->x + name_node->x),
                            static_cast<f32>(row_y + node->y + name_node->y),
                            0.0f, 0.0f, fade);              // 0x001F0E8C
            const Npc2dLayoutNode* icon_node =
                UiLayout_GetNode(0x24, 0x177);              // 0x001F0E90
            UiParty_DrawDemonBars(
                static_cast<s16>(work->rows_9010[i]),
                row_x + node->x + icon_node->x,
                row_y + node->y + icon_node->y, 0x74, 0.0f, 0);
            const Npc2dLayoutNode* id_node =
                UiLayout_GetNode(0x24, 0x17C);              // 0x001F0ED4
            UiFont_DrawFormatted(1,
                                 row_x + node->x + id_node->x,
                                 row_y + node->y + id_node->y,
                                 1, 4, 0x79, "%d",
                                 Party_GetDemonActiveIndex(
                                     static_cast<s16>(work->rows_9010[i])));
        } else {
            // 0x001F0F44..0x001F0FB4
            UiFont_FormatString(text, "%s", kFusionDash);
            const Npc2dLayoutNode* dash_node =
                UiLayout_GetNode(0x24, 0x178);
            UiFont_DrawText(2, 0xFFu, text,
                            static_cast<f32>(row_x + node->x + dash_node->x),
                            static_cast<f32>(row_y + node->y + dash_node->y),
                            0.0f, 0.0f, fade);
        }

        if (mode == 1) {                                    // 0x001F0F34..0x001F0F40
            if (work->field_3fc >= 5) {
                const s32 sel = UiListCursor_GetSelectedRow(cursor) +
                                UiListCursor_GetScrollOffset(cursor);
                if (work->rows_9010[i] == work->rows_9020[sel]) {
                    UiSprite_SetGlobalAlpha(*reinterpret_cast<const f32*>(
                        reinterpret_cast<const u8*>(work) + 0x36C + 0x20));
                    GpuModeSlotSet(static_cast<u32>(
                        reinterpret_cast<std::uintptr_t>(
                            UiGpu_SetRenderMode(6, 1, 0)))); // 0x001F101C
                    UiSprite_DrawNode(2, 0x24, 0x173,
                                      row_x + node->x, row_y + node->y, 0x65);
                    GpuModeSlotSet(static_cast<u32>(
                        reinterpret_cast<std::uintptr_t>(
                            UiGpu_SetRenderMode(6, 7, 0)))); // 0x001F1094
                }
            }
        }
        UiSprite_SetGlobalAlpha(1.0f);                      // 0x001F10D0
    }

    // 0x001F10E4..0x001F1390: inherited-skill pair list.
    FusionPairBuffer pairs{};
    Item_BuildFusionPairList(*reinterpret_cast<u16*>(row), row[3],
                             work->rows_9010, &pairs, 0);   // 0x0026ac34
    s32 pair_count = 0;
    while (pair_count < 8) {
        if (pairs.values[pair_count] == 0) {
            break;
        }
        if (pairs.values[pair_count + 1] == 0) {
            ++pair_count;
            break;
        }
        pair_count += 2;
    }

    if (pair_count > 0) {
        for (s32 i = 0; i < pair_count; ++i) {
            node = UiLayout_GetNode(0x24, 0x193 + i);       // 0x001F1298
            UiSprite_DrawNode(2, 0x24, 0x18E, x + node->x, y + node->y, 0x65);
            UiSprite_DrawNode(2, 0x24, 0x18F, x + node->x, y + node->y, 0x65);
            UiSprite_DrawNode(2, 0x24, 0x190, x + node->x, y + node->y, 0x65);
            UiSprite_DrawNode(2, 0x24, 0x191, x + node->x, y + node->y, 0x6A);
            const Npc2dLayoutNode* pair_node =
                UiLayout_GetNode(0x24, 0x192);              // 0x001F1340
            UiParty_DrawDemonBars(static_cast<s16>(pairs.values[i]),
                                  x + node->x + pair_node->x,
                                  y + node->y + pair_node->y,
                                  0x6F, 0.0f, 0);
        }
    } else {
        // 0x001F1164..0x001F128C
        node = UiLayout_GetNode(0x24, 0x197);
        UiSprite_DrawNode(2, 0x24, 0x16F, x + node->x, y + node->y, 0x65);
        UiSprite_DrawNode(2, 0x24, 0x170, x + node->x, y + node->y, 0x65);
        UiSprite_DrawNode(2, 0x24, 0x16B, x + node->x, y + node->y, 0x65);
        const Npc2dLayoutNode* money_node =
            UiLayout_GetNode(0x24, 0x178);                  // 0x001F11E4
        UiFont_FormatString(text, "%s", kFusionMoney);
        UiFont_DrawText(2, 0x323232FFu, text,
                        static_cast<f32>(x + node->x + money_node->x),
                        static_cast<f32>(y + node->y + money_node->y),
                        0.0f, 0.0f, 1.0f);                  // 0x001F1280
    }

    // 0x001F1394..0x001F161C: eight lower rows.
    const s32 lower_scroll = UiListCursor_GetScrollOffset(cursor);
    for (s32 i = 0; i < 8; ++i) {
        if (has_target != 0 && UiListCursor_GetSelectedRow(cursor) == i) {
            continue;                                       // 0x001F13A4..0x001F13C0
        }
        node = UiLayout_GetNode(0x24, 0x185 + i);           // 0x001F13C4
        UiSprite_DrawNode(2, 0x24, 0x16F, x + node->x, y + node->y, 0x65);
        UiSprite_DrawNode(2, 0x24, 0x170, x + node->x, y + node->y, 0x65);
        UiSprite_DrawNode(2, 0x24, 0x176, x + node->x, y + node->y, 0x6F);

        if (UiList_CountActiveRows(party_list) > i) {       // 0x001F1450
            const u16 entry = work->rows_9020[lower_scroll + i];
            const u32 color =
                UiArray_ContainsU16(work->rows_9010, 8, entry) != 0
                    ? 0x008400FFu : 0xFFFFFFFFu;            // 0x001F14F8..0x001F1504
            UiFont_FormatString(text, "%s", Item_GetNameString(entry));
            const Npc2dLayoutNode* name_node =
                UiLayout_GetNode(0x24, 0x178);              // 0x001F151C
            UiFont_DrawText(2, color, text,
                            static_cast<f32>(x + node->x + name_node->x),
                            static_cast<f32>(y + node->y + name_node->y),
                            0.0f, 0.0f, 1.0f);              // 0x001F1570
            const Npc2dLayoutNode* icon_node =
                UiLayout_GetNode(0x24, 0x177);              // 0x001F1574
            UiParty_DrawDemonBars(static_cast<s16>(entry),
                                  x + node->x + icon_node->x,
                                  y + node->y + icon_node->y,
                                  0x74, 0.0f, 0);
            const Npc2dLayoutNode* id_node =
                UiLayout_GetNode(0x24, 0x17C);              // 0x001F15B4
            UiFont_DrawFormatted(1,
                                 x + node->x + id_node->x,
                                 y + node->y + id_node->y,
                                 1, 4, 0x79, "%d",
                                 Party_GetDemonActiveIndex(
                                     static_cast<s16>(entry)));
        }
    }

    // 0x001F1620..0x001F1A2C: selected lower-row detail.
    const s32 lower_selected = UiListCursor_GetScrollOffset(cursor) +
                               UiListCursor_GetSelectedRow(cursor);
    if (has_target != 0) {
        node = UiLayout_GetNode(0x24, 0x1A7 +
                                UiListCursor_GetSelectedRow(cursor)); // 0x001F164C
        UiSprite_SetGlobalAlpha(*reinterpret_cast<const f32*>(
            reinterpret_cast<const u8*>(work) + 0x24 + 0x20)); // 0x001F1664
        UiSprite_DrawNode(2, 0x24, 0x198, x + node->x, y + node->y, 0x79);
        UiSprite_DrawNode(2, 0x24, 0x199, x + node->x, y + node->y, 0x79);
        UiSprite_DrawNode(2, 0x24, 0x19A, x + node->x, y + node->y, 0x79);
        UiSprite_SetGlobalAlpha(1.0f);                      // 0x001F16E4
        UiSprite_DrawNode(2, 0x24, 0x19B, x + node->x, y + node->y, 0x7E);

        const s16 touch = *reinterpret_cast<const s16*>(
            reinterpret_cast<const u8*>(work) + 0x400 + 0x38 +
            UiListCursor_GetSelectedRow(cursor) * 2);       // 0x001F1720
        const s32 touch_state = UiTouch_GetRegionTouchState(touch);
        if (touch_state == 1 || touch_state == 2 || touch_state == 6) {
            UiSprite_DrawNode(2, 0x24, 0x19D, x + node->x, y + node->y, 0x7E);
        } else {
            UiSprite_DrawNode(2, 0x24, 0x19C, x + node->x, y + node->y, 0x7E);
        }

        const Npc2dLayoutNode* panel_node =
            UiLayout_GetNode(0x24, 0x19C);                  // 0x001F1768
        const s16* rect = reinterpret_cast<const s16*>(panel_node->extra);
        GpuModeSlotSet(3);                                  // 0x001F1780
        const Npc2dLayoutNode* detail_node =
            UiLayout_GetNode(0x24, 0x1A7 +
                             UiListCursor_GetSelectedRow(cursor));
        UiScissor_SetRect(x + detail_node->x + panel_node->x,
                          y + detail_node->y + panel_node->y,
                          rect[0], rect[1], 1);             // 0x001F17EC
        GpuModeSlotSet(0);                                  // 0x001F183C

        node = panel_node;                                  // r7 := node 0x19C
        UiSprite_DrawNode(2, 0x24, 0x19F, x + node->x, y + node->y, 0x83);
        UiSprite_DrawNode(2, 0x24, 0x1A0, x + node->x, y + node->y, 0x83);

        const u16 entry = work->rows_9020[lower_selected];
        const u32 color = UiArray_ContainsU16(work->rows_9010, 8, entry) != 0
                              ? 0x008400FFu : 0xFFFFFFFFu; // 0x001F18D4..0x001F18DC
        UiFont_FormatString(text, "%s", Item_GetNameString(entry));
        const Npc2dLayoutNode* name_node =
            UiLayout_GetNode(0x24, 0x1A2);                  // 0x001F1904
        UiFont_DrawText(3, color, text,
                        static_cast<f32>(x + node->x + name_node->x),
                        static_cast<f32>(y + node->y + name_node->y),
                        0.0f, 0.0f, 1.0f);                  // 0x001F1950
        const Npc2dLayoutNode* icon_node =
            UiLayout_GetNode(0x24, 0x1A1);                  // 0x001F1958
        UiParty_DrawDemonBars(static_cast<s16>(entry),
                              x + node->x + icon_node->x,
                              y + node->y + icon_node->y,
                              0x8D, 0.0f, 0);
        const Npc2dLayoutNode* id_node =
            UiLayout_GetNode(0x24, 0x1A6);                  // 0x001F19DC
        UiFont_DrawFormatted(1,
                             x + node->x + id_node->x,
                             y + node->y + id_node->y,
                             1, 4, 0x8D, "%d",
                             Party_GetDemonActiveIndex(static_cast<s16>(entry)));
    }

    // 0x001F1A30..0x001F1AA0: scrollbar.  The twelve stack words are the
    // node-id pair table (0x2A/0x2B/0x2C/0x26/0x28/0x27/0x29), the three
    // workspace heights at +0x476/+0x472/+0x474, prio 0x97 and the trailing 0.
    UiScrollBar_Draw(cursor, x, y, 0x24,
                     0x2A, 0x2B, 0x2C, 0x26, 0x28, 0x27, 0x29,
                     work->field_476, work->field_472, 0x97,
                     work->field_474, 0);
    (void)slide_dir;
}

} // namespace smt4::ui
