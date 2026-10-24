#include "ui/ui_runtime.h"
#include "engine/asd_symbols.h"
#include "script/script_extras.h"
#include <cstring>

namespace smt4::ui {

using engine::Npc2dLayoutNode;

UiPartRenderState g_UiPartRenderState{};        // 0x004EA81C (BSS)

namespace {

// Canonical 0x002BF6D0 returns `const void*`; this TU uses the
// offset-compatible Npc2dLayoutNode view.
inline const Npc2dLayoutNode* LayoutNode(u32 group, u32 node) {
    return static_cast<const Npc2dLayoutNode*>(UiLayout_GetNode(group, node));
}

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

    s32   UiArray_ContainsU16(const u16* values, s32 count, u16 value);         // 0x0029d080
    s32   UiTouch_GetRegionTouchState(s16 handle);                              // 0x0029d8fc
    void  UiScissor_SetRect(s32 x, s32 y, s32 w, s32 h, s32 enable);            // 0x0029a418
    void  UiScrollBar_Draw(UiListCursor* cursor, s32 x, s32 y, u32 group,
                           s32 up_h, s32 down_h, s32 a6, s32 a7, s32 a8,
                           s32 a9, s32 a10, s32 btn_h, s32 up_h2,
                           s32 down_h2, s32 prio, s32 a15);                     // 0x00290c38

    void  UiSkill_DrawItemIconAndCount(s32 item_id, s32 x, s32 y,
                                       s32 prio, s32 a4);                       // 0x002b6a98
    // 5th/6th arguments are the integer draw-bars gate and row offset.
    void  UiParty_DrawDemonBars(s16 demon_id, s32 x, s32 y, s32 prio,
                                s32 draw_bars, s32 a5);                         // 0x002b6f74
    s32   Party_GetDemonActiveIndex(s16 demon_id);                              // 0x0029abc0
    const char* Item_GetNameString(u16 item_id);                                // 0x002bcff0
    const char* Item_GetShortNameString(u16 item_id);                           // 0x002bd258
    const char* Item_GetDescriptionString(u16 item_id, s32 mode);                // 0x002bd020

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

/** The UI render-mode ring lives at `g_AsdGpuState + 0x1000 + slot_offset`:
 *  the quest preview and the fusion row use 0x2AC (0x001985A4 / 0x001F1020),
 *  while the fusion selected-detail scissor path uses 0x30C (0x001F1784 /
 *  0x001F1840).  The low word is the ring cursor, the value is stored at
 *  +8+index*4 and the +0x1C callback runs when the slot changes or +0x18 is
 *  set. */
void GpuModeSlotSet(u32 slot_offset, u32 value) {
    u8* slot = g_AsdGpuState + 0x1000 + slot_offset;
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

u32 ByteSwap32(u32 value) {
    return ((value >> 24) & 0xFF) | ((value >> 8) & 0xFF00) |
           ((value << 8) & 0xFF0000) | ((value << 24) & 0xFF000000);
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
    const u32 color = ByteSwap32(ctx->color);            // 0x0026855C..0x002685A8
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
__attribute__((naked)) void ui_func_00267fb0(UiPartRenderContext* ctx, f32 scale) {
    asm volatile(
        ".word 0xe92d4ff0\n"
        ".word 0xe1a09000\n"
        ".word 0xed2d8b10\n"
        ".word 0xeeb0aa40\n"
        ".word 0xe24ddf43\n"
        ".word 0xe590804c\n"
        ".word 0xe5900004\n"
        ".word 0xed9f0ad2\n"
        ".word 0xe20040ff\n"
        ".word 0xe1a0c800\n"
        ".word 0xe1a03c20\n"
        ".word 0xe1a0cc2c\n"
        ".word 0xee023a10\n"
        ".word 0xe1a01400\n"
        ".word 0xee00ca90\n"
        ".word 0xee014a90\n"
        ".word 0xe1a01c21\n"
        ".word 0xee011a10\n"
        ".word 0xeef82a42\n"
        ".word 0xe59f031c\n"
        ".word 0xeeb82a60\n"
        ".word 0xeef80a61\n"
        ".word 0xeeb81a41\n"
        ".word 0xee228a80\n"
        ".word 0xee229a00\n"
        ".word 0xee609a80\n"
        ".word 0xee618a00\n"
        ".word 0xec808a04\n"
        ".word 0xe5985008\n"
        ".word 0xe3550000\n"
        ".word 0x15980010\n"
        ".word 0x13500000\n"
        ".word 0x0a000173\n"
        ".word 0xe1d900bc\n"
        ".word 0xe5984018\n"
        ".word 0xe350000a\n"
        ".word 0x379ff100\n"
        ".word 0xea00016e\n"
        ".word 0x00268604\n"
        ".word 0x00268070\n"
        ".word 0x00268610\n"
        ".word 0x00268604\n"
        ".word 0x00268070\n"
        ".word 0x00268eec\n"
        ".word 0x00269050\n"
        ".word 0x002691bc\n"
        ".word 0x00268604\n"
        ".word 0x00268070\n"
        ".word 0xe2890054\n"
        ".word 0xe5991050\n"
        ".word 0xe3a06000\n"
        ".word 0xec900a02\n"
        ".word 0xe28d2090\n"
        ".word 0xe5980020\n"
        ".word 0xee208a0a\n"
        ".word 0xee608a8a\n"
        ".word 0xe58d0018\n"
        ".word 0xe591b00c\n"
        ".word 0xe3a01001\n"
        ".word 0xe1a0000b\n"
        ".word 0xebffbd40\n"
        ".word 0xe28d2c01\n"
        ".word 0xe3a01002\n"
        ".word 0xe1a0000b\n"
        ".word 0xebffbd3c\n"
        ".word 0xe28d2080\n"
        ".word 0xe3a01004\n"
        ".word 0xe1a0000b\n"
        ".word 0xebffbd38\n"
        ".word 0xe28d2088\n"
        ".word 0xe3a01020\n"
        ".word 0xe1a0000b\n"
        ".word 0xebffbd34\n"
        ".word 0xe598000c\n"
        ".word 0xe3100001\n"
        ".word 0x0a000093\n"
        ".word 0xe28d10e8\n"
        ".word 0xe1a00008\n"
        ".word 0xebff9e6d\n"
        ".word 0xe28d1030\n"
        ".word 0xe1a00008\n"
        ".word 0xebff9e66\n"
        ".word 0xe28da0e8\n"
        ".word 0xe59f7220\n"
        ".word 0xe89a100e\n"
        ".word 0xe2870c01\n"
        ".word 0xe880100e\n"
        ".word 0xeb00eb82\n"
        ".word 0xe59d1030\n"
        ".word 0xe2870f51\n"
        ".word 0xe3550000\n"
        ".word 0xe5871170\n"
        ".word 0xe59d1034\n"
        ".word 0xe3a03000\n"
        ".word 0xe5871174\n"
        ".word 0xe59d1038\n"
        ".word 0xe5871178\n"
        ".word 0xe59d103c\n"
        ".word 0xe587117c\n"
        ".word 0xedd7aa50\n"
        ".word 0xedd7ba53\n"
        ".word 0xedd7fa58\n"
        ".word 0xed97fa59\n"
        ".word 0xec90ca02\n"
        ".word 0xe2870e15\n"
        ".word 0xec90da04\n"
        ".word 0xe5970168\n"
        ".word 0xe58d0050\n"
        ".word 0xe597016c\n"
        ".word 0xe58d0054\n"
        ".word 0xe5970170\n"
        ".word 0xe58d0058\n"
        ".word 0xe5970174\n"
        ".word 0xe58d005c\n"
        ".word 0xe5970178\n"
        ".word 0xe58d0060\n"
        ".word 0xc59f01a0\n"
        ".word 0xed97ba5f\n"
        ".word 0xc180ef00\n"
        ".word 0xda00011c\n"
        ".word 0xe5941010\n"
        ".word 0xe3510000\n"
        ".word 0xba0000e9\n"
        ".word 0xe28d1050\n"
        ".word 0xe59fc17c\n"
        ".word 0xec910a05\n"
        ".word 0xe28c1f5a\n"
        ".word 0xe28c7c01\n"
        ".word 0xedccaa50\n"
        ".word 0xedccba53\n"
        ".word 0xedccfa58\n"
        ".word 0xed8cfa59\n"
        ".word 0xed8cba5f\n"
        ".word 0xe1a02007\n"
        ".word 0xec810a05\n"
        ".word 0xe28c1f51\n"
        ".word 0xec81ca02\n"
        ".word 0xe28c1e15\n"
        ".word 0xec81da04\n"
        ".word 0xe28c1d05\n"
        ".word 0xe28ccc01\n"
        ".word 0xec940a04\n"
        ".word 0xec870a04\n"
        ".word 0xed970a01\n"
        ".word 0xedd13a04\n"
        ".word 0xed915a05\n"
        ".word 0xedd16a06\n"
        ".word 0xed919a07\n"
        ".word 0xee603a23\n"
        ".word 0xee205a05\n"
        ".word 0xee606a26\n"
        ".word 0xee200a09\n"
        ".word 0xe2817030\n"
        ".word 0xedd19a0b\n"
        ".word 0xed91aa03\n"
        ".word 0xedd20a02\n"
        ".word 0xed921a00\n"
        ".word 0xed914a08\n"
        ".word 0xedd14a00\n"
        ".word 0xed917a0a\n"
        ".word 0xedd17a02\n"
        ".word 0xee000aa9\n"
        ".word 0xecd71a04\n"
        ".word 0xee403a84\n"
        ".word 0xee406a87\n"
        ".word 0xedd15a09\n"
        ".word 0xed916a01\n"
        ".word 0xee411a24\n"
        ".word 0xee013a0a\n"
        ".word 0xee412a27\n"
        ".word 0xee012a06\n"
        ".word 0xee005aa5\n"
        ".word 0xe28d7090\n"
        ".word 0xee730aa1\n"
        ".word 0xee300a03\n"
        ".word 0xee761aa2\n"
        ".word 0xee351a02\n"
        ".word 0xed820a03\n"
        ".word 0xecc20a03\n"
        ".word 0xe59d1090\n"
        ".word 0xec9c0a03\n"
        ".word 0xed810a00\n"
        ".word 0xe59d1090\n"
        ".word 0xedc10a01\n"
        ".word 0xe59d1090\n"
        ".word 0xed811a02\n"
        ".word 0xe8970006\n"
        ".word 0xe0811002\n"
        ".word 0xe58d1090\n"
        ".word 0xe5942014\n"
        ".word 0xe59d1100\n"
        ".word 0xe6bf7f32\n"
        ".word 0xe6bfaf32\n"
        ".word 0xe6bfcf32\n"
        ".word 0xe6bf2f32\n"
        ".word 0xe1a07827\n"
        ".word 0xe1a0a42a\n"
        ".word 0xe1a0cc2c\n"
        ".word 0xe5c1c000\n"
        ".word 0xe5c17001\n"
        ".word 0xe28d7c01\n"
        ".word 0xe5c1a002\n"
        ".word 0xe5c12003\n"
        ".word 0xe8970006\n"
        ".word 0xe0811002\n"
        ".word 0xe58d1100\n"
        ".word 0xed940a07\n"
        ".word 0xee101a10\n"
        ".word 0xe1510000\n"
        ".word 0xee101a10\n"
        ".word 0xda00006a\n"
        ".word 0xe1510000\n"
        ".word 0xcddf0a09\n"
        ".word 0xda000070\n"
        ".word 0xee300a60\n"
        ".word 0xee101a10\n"
        ".word 0xe1510000\n"
        ".word 0xcafffffb\n"
        ".word 0xea00006b\n"
        ".word 0x3b808081\n"
        ".word 0x004ea91c\n"
        ".word 0x004ea81c\n"
        ".word 0x40490fdb\n"
        ".word 0x40c90fdb\n"
        ".word 0xe3550000\n"
        ".word 0xe3a03000\n"
        ".word 0xda0000b1\n"
        ".word 0xe51f001c\n"
        ".word 0xed5f0a07\n"
        ".word 0xe180ef00\n"
        ".word 0xe5941010\n"
        ".word 0xe3510000\n"
        ".word 0xba00004f\n"
        ".word 0xe59d1090\n"
        ".word 0xed940a00\n"
        ".word 0xe28d7090\n"
        ".word 0xed810a00\n"
        ".word 0xe59d1090\n"
        ".word 0xe5942004\n"
        ".word 0xe5812004\n"
        ".word 0xe59d1090\n"
        ".word 0xe5942008\n"
        ".word 0xe5812008\n"
        ".word 0xe8970006\n"
        ".word 0xe0811002\n"
        ".word 0xe58d1090\n"
        ".word 0xe5942014\n"
        ".word 0xe59d1100\n"
        ".word 0xe6bfcf32\n"
        ".word 0xe6bf7f32\n"
        ".word 0xe6bfaf32\n"
        ".word 0xe1a0cc2c\n"
        ".word 0xe1a07827\n"
        ".word 0xe5c1c000\n"
        ".word 0xe5c17001\n"
        ".word 0xe6bf2f32\n"
        ".word 0xe1a0a42a\n"
        ".word 0xe28d7c01\n"
        ".word 0xe5c1a002\n"
        ".word 0xe5c12003\n"
        ".word 0xe8970006\n"
        ".word 0xe0811002\n"
        ".word 0xe58d1100\n"
        ".word 0xed940a07\n"
        ".word 0xee101a10\n"
        ".word 0xe1510000\n"
        ".word 0xee101a10\n"
        ".word 0xda000006\n"
        ".word 0xe1510000\n"
        ".word 0xda00000c\n"
        ".word 0xee300a60\n"
        ".word 0xee101a10\n"
        ".word 0xe1510000\n"
        ".word 0xcafffffb\n"
        ".word 0xea000007\n"
        ".word 0xe151000e\n"
        ".word 0x8e101a10\n"
        ".word 0x8151000e\n"
        ".word 0x9a000003\n"
        ".word 0xee300a20\n"
        ".word 0xee101a10\n"
        ".word 0xe151000e\n"
        ".word 0x8afffffb\n"
        ".word 0xed840a07\n"
        ".word 0xe59d1088\n"
        ".word 0xe28d7088\n"
        ".word 0xed810a00\n"
        ".word 0xe8970006\n"
        ".word 0xe0811002\n"
        ".word 0xe58d1088\n"
        ".word 0xed940a06\n"
        ".word 0xe59d1080\n"
        ".word 0xee281a00\n"
        ".word 0xee280a80\n"
        ".word 0xed811a00\n"
        ".word 0xe59d1080\n"
        ".word 0xed810a01\n"
        ".word 0xe598100c\n"
        ".word 0xe3110002\n"
        ".word 0x0a000007\n"
        ".word 0xedd41a08\n"
        ".word 0xe59d1080\n"
        ".word 0xee211a21\n"
        ".word 0xed811a00\n"
        ".word 0xed941a09\n"
        ".word 0xe59d1080\n"
        ".word 0xee200a01\n"
        ".word 0xed810a01\n"
        ".word 0xe28d7080\n"
        ".word 0xe2866001\n"
        ".word 0xe8970006\n"
        ".word 0xe0811002\n"
        ".word 0xe58d1080\n"
        ".word 0xe2833001\n"
        ".word 0xe1530005\n"
        ".word 0xe2844028\n"
        ".word 0xbaffffa8\n"
        ".word 0xea00002a\n"
        ".word 0xe151000e\n"
        ".word 0x8e101a10\n"
        ".word 0x8151000e\n"
        ".word 0x8d5f0a64\n"
        ".word 0x9a000003\n"
        ".word 0xee300a20\n"
        ".word 0xee101a10\n"
        ".word 0xe151000e\n"
        ".word 0x8afffffb\n"
        ".word 0xed840a07\n"
        ".word 0xe59d2088\n"
        ".word 0xe28d7088\n"
        ".word 0xed820a00\n"
        ".word 0xe8970006\n"
        ".word 0xe0811002\n"
        ".word 0xe58d1088\n"
        ".word 0xed940a06\n"
        ".word 0xe59d1080\n"
        ".word 0xee680a00\n"
        ".word 0xee280a80\n"
        ".word 0xedc10a00\n"
        ".word 0xe59d1080\n"
        ".word 0xed810a01\n"
        ".word 0xe598100c\n"
        ".word 0xe3110002\n"
        ".word 0x0a000007\n"
        ".word 0xed941a08\n"
        ".word 0xe59d1080\n"
        ".word 0xee600a81\n"
        ".word 0xedc10a00\n"
        ".word 0xedd40a09\n"
        ".word 0xe59d1080\n"
        ".word 0xee200a20\n"
        ".word 0xed810a01\n"
        ".word 0xe28d7080\n"
        ".word 0xe2866001\n"
        ".word 0xe8970006\n"
        ".word 0xe0811002\n"
        ".word 0xe58d1080\n"
        ".word 0xe2833001\n"
        ".word 0xe1530005\n"
        ".word 0xe2844028\n"
        ".word 0xbaffff0e\n"
        ".word 0xe3560000\n"
        ".word 0x0a000029\n"
        ".word 0xe5990004\n"
        ".word 0xe3c9c0ff\n"
        ".word 0xe6bf2f30\n"
        ".word 0xe6bf3f30\n"
        ".word 0xe6bf4f30\n"
        ".word 0xe1a01c22\n"
        ".word 0xe1a03823\n"
        ".word 0xe181100c\n"
        ".word 0xe1a03403\n"
        ".word 0xe203ccff\n"
        ".word 0xe1a02424\n"
        ".word 0xe3c11cff\n"
        ".word 0xe1a03802\n"
        ".word 0xe6bf2f30\n"
        ".word 0xe181100c\n"
        ".word 0xe20308ff\n"
        ".word 0xe3c118ff\n"
        ".word 0xe1800001\n"
        ".word 0xe3c004ff\n"
        ".word 0xe1804c02\n"
        ".word 0xe1a00008\n"
        ".word 0xebfec472\n"
        ".word 0xe3500000\n"
        ".word 0xe320f000\n"
        ".word 0x0a000005\n"
        ".word 0xe59b10a8\n"
        ".word 0xe3a02008\n"
        ".word 0xe3811002\n"
        ".word 0xe58b10a8\n"
        ".word 0xe28b10ac\n"
        ".word 0xeb01540d\n"
        ".word 0xe5ab6060\n"
        ".word 0xe58b4004\n"
        ".word 0xe59d0018\n"
        ".word 0xe5900054\n"
        ".word 0xe6ff0070\n"
        ".word 0xebffbb8a\n"
        ".word 0xe59d0018\n"
        ".word 0xe5901054\n"
        ".word 0xe5990050\n"
        ".word 0xe6ff1071\n"
        ".word 0xebffb9a2\n"
        ".word 0xe28ddf43\n"
        ".word 0xecbd8b10\n"
        ".word 0xe8bd8ff0\n"
        ".word 0xe5990050\n"
        ".word 0xe3a07000\n"
        ".word 0xe28d2090\n"
        ".word 0xe3a01001\n"
        ".word 0xe590600c\n"
        ".word 0xe58d602c\n"
        ".word 0xe5990044\n"
        ".word 0xe58d000c\n"
        ".word 0xe5980020\n"
        ".word 0xe58d0018\n"
        ".word 0xe1a00006\n"
        ".word 0xebffbbd9\n"
        ".word 0xe59d002c\n"
        ".word 0xe28d2c01\n"
        ".word 0xe3a01002\n"
        ".word 0xebffbbd5\n"
        ".word 0xe59d002c\n"
        ".word 0xe28d2080\n"
        ".word 0xe3a01004\n"
        ".word 0xebffbbd1\n"
        ".word 0xe59d002c\n"
        ".word 0xe28d2088\n"
        ".word 0xe3a01020\n"
        ".word 0xebffbbcd\n"
        ".word 0xe59d002c\n"
        ".word 0xe28d2020\n"
        ".word 0xe3a01080\n"
        ".word 0xebffbbc9\n"
        ".word 0xe59d000c\n"
        ".word 0xe59d602c\n"
        ".word 0xe3a01000\n"
        ".word 0xebfde492\n"
        ".word 0xe58600b4\n"
        ".word 0xe320f000\n"
        ".word 0xeb00042e\n"
        ".word 0xe598000c\n"
        ".word 0xe3100001\n"
        ".word 0x0a000102\n"
        ".word 0xe28d10e8\n"
        ".word 0xe1a00008\n"
        ".word 0xebff9cfb\n"
        ".word 0xe28d1030\n"
        ".word 0xe1a00008\n"
        ".word 0xebff9cf4\n"
        ".word 0xe28d60e8\n"
        ".word 0xe51fa3a8\n"
        ".word 0xe896100e\n"
        ".word 0xe28a0c01\n"
        ".word 0xe880100e\n"
        ".word 0xeb00ea10\n"
        ".word 0xe59d1030\n"
        ".word 0xe28a0d05\n"
        ".word 0xe3550000\n"
        ".word 0xe58a1170\n"
        ".word 0xe59d1034\n"
        ".word 0xe3a06000\n"
        ".word 0xe58a1174\n"
        ".word 0xe59d1038\n"
        ".word 0xe58a1178\n"
        ".word 0xe59d103c\n"
        ".word 0xe58a117c\n"
        ".word 0xed9aea53\n"
        ".word 0xed9aca54\n"
        ".word 0xeddada55\n"
        ".word 0xeddaca56\n"
        ".word 0xecd0aa03\n"
        ".word 0xe59a015c\n"
        ".word 0xe58d0048\n"
        ".word 0xe59a0164\n"
        ".word 0xed9afa58\n"
        ".word 0xe58d004c\n"
        ".word 0xe59a016c\n"
        ".word 0xeddaea5a\n"
        ".word 0xe58d0054\n"
        ".word 0xe59a0170\n"
        ".word 0xe58d0058\n"
        ".word 0xe59a0174\n"
        ".word 0xe58d005c\n"
        ".word 0xe59a0178\n"
        ".word 0xe58d0060\n"
        ".word 0xed9ada5f\n"
        ".word 0xdaffffaa\n"
        ".word 0xe51f8438\n"
        ".word 0xeddffad1\n"
        ".word 0xed9f8ad1\n"
        ".word 0xeddf8ad1\n"
        ".word 0xe5941010\n"
        ".word 0xe3510000\n"
        ".word 0xba0001b3\n"
        ".word 0xe59d000c\n"
        ".word 0xebffba92\n"
        ".word 0xe59d000c\n"
        ".word 0xe28d10b0\n"
        ".word 0xebffba1c\n"
        ".word 0xe28d0048\n"
        ".word 0xe51fc470\n"
        ".word 0xec900a02\n"
        ".word 0xe28d0054\n"
        ".word 0xe28c3f5b\n"
        ".word 0xec901a04\n"
        ".word 0xe28c0c01\n"
        ".word 0xe1a02000\n"
        ".word 0xed8cea53\n"
        ".word 0xed8cca54\n"
        ".word 0xedccda55\n"
        ".word 0xedccca56\n"
        ".word 0xed8c0a57\n"
        ".word 0xed8cfa58\n"
        ".word 0xedcc0a59\n"
        ".word 0xedccea5a\n"
        ".word 0xed8cda5f\n"
        ".word 0xe1a0b000\n"
        ".word 0xec831a04\n"
        ".word 0xe28c3d05\n"
        ".word 0xe28c1d05\n"
        ".word 0xe1a0a002\n"
        ".word 0xecc3aa03\n"
        ".word 0xe28cee11\n"
        ".word 0xe28c3e11\n"
        ".word 0xec940a04\n"
        ".word 0xec800a04\n"
        ".word 0xe58d006c\n"
        ".word 0xe28c0e15\n"
        ".word 0xedd20a01\n"
        ".word 0xed9c9a57\n"
        ".word 0xeddc4a58\n"
        ".word 0xeddc5a59\n"
        ".word 0xee209a89\n"
        ".word 0xec903a03\n"
        ".word 0xe2810030\n"
        ".word 0xed9c6a51\n"
        ".word 0xeddc7a5b\n"
        ".word 0xee203a83\n"
        ".word 0xee603aa3\n"
        ".word 0xee204a84\n"
        ".word 0xedd20a02\n"
        ".word 0xedd19a03\n"
        ".word 0xed9c5a50\n"
        ".word 0xeddc6a5a\n"
        ".word 0xed9c7a52\n"
        ".word 0xee009aa7\n"
        ".word 0xec901a04\n"
        ".word 0xee003aa4\n"
        ".word 0xee403aa5\n"
        ".word 0xedd24a00\n"
        ".word 0xee004aa6\n"
        ".word 0xe28c0c01\n"
        ".word 0xee441a86\n"
        ".word 0xee442aa9\n"
        ".word 0xee041a85\n"
        ".word 0xee042a87\n"
        ".word 0xee730aa1\n"
        ".word 0xee791a22\n"
        ".word 0xee330a01\n"
        ".word 0xee341a02\n"
        ".word 0xec820a04\n"
        ".word 0xe59d1020\n"
        ".word 0xeddd1a32\n"
        ".word 0xec9b0a03\n"
        ".word 0xe28db020\n"
        ".word 0xedc11a00\n"
        ".word 0xe59d1020\n"
        ".word 0xe59d20cc\n"
        ".word 0xe5812004\n"
        ".word 0xe59d1020\n"
        ".word 0xe59d20d0\n"
        ".word 0xe5812008\n"
        ".word 0xe59d1020\n"
        ".word 0xe59d20d4\n"
        ".word 0xe581200c\n"
        ".word 0xe89b0006\n"
        ".word 0xe28db090\n"
        ".word 0xe0811002\n"
        ".word 0xe58d1020\n"
        ".word 0xe59d1090\n"
        ".word 0xed810a00\n"
        ".word 0xe59d1090\n"
        ".word 0xedc10a01\n"
        ".word 0xe59d1090\n"
        ".word 0xed811a02\n"
        ".word 0xe89b0006\n"
        ".word 0xe0811002\n"
        ".word 0xe58d1090\n"
        ".word 0xe5941014\n"
        ".word 0xe1a02401\n"
        ".word 0xe1a02c22\n"
        ".word 0xee002a10\n"
        ".word 0xe1a02801\n"
        ".word 0xe1a02c22\n"
        ".word 0xee002a90\n"
        ".word 0xe1a02c21\n"
        ".word 0xee012a10\n"
        ".word 0xe20110ff\n"
        ".word 0xee011a90\n"
        ".word 0xeeb80a40\n"
        ".word 0xeef80a60\n"
        ".word 0xe28e2004\n"
        ".word 0xeeb81a41\n"
        ".word 0xeef81a61\n"
        ".word 0xee200a08\n"
        ".word 0xee600a88\n"
        ".word 0xee211a08\n"
        ".word 0xee611a88\n"
        ".word 0xed8e1a00\n"
        ".word 0xedce1a03\n"
        ".word 0xec820a02\n"
        ".word 0xe59d10dc\n"
        ".word 0xe1a0c401\n"
        ".word 0xe1a02801\n"
        ".word 0xe1a0cc2c\n"
        ".word 0xee00ca90\n"
        ".word 0xe1a02c22\n"
        ".word 0xe1a0cc21\n"
        ".word 0xe20110ff\n"
        ".word 0xee012a90\n"
        ".word 0xee011a10\n"
        ".word 0xee00ca10\n"
        ".word 0xeef80a60\n"
        ".word 0xe59d106c\n"
        ".word 0xeef81a61\n"
        ".word 0xeeb82a41\n"
        ".word 0xeeb80a40\n"
        ".word 0xee600a88\n"
        ".word 0xee211a88\n"
        ".word 0xee621a08\n"
        ".word 0xee200a08\n"
        ".word 0xec810a04\n"
        ".word 0xedd00a00\n"
        ".word 0xed930a00\n"
        ".word 0xee200a80\n"
        ".word 0xed800a00\n"
        ".word 0xed900a01\n"
        ".word 0xedd30a01\n"
        ".word 0xee200a20\n"
        ".word 0xed800a01\n"
        ".word 0xedd00a02\n"
        ".word 0xed930a02\n"
        ".word 0xee200a80\n"
        ".word 0xed800a02\n"
        ".word 0xedd30a03\n"
        ".word 0xed900a03\n"
        ".word 0xee200a20\n"
        ".word 0xed800a03\n"
        ".word 0xec9a0a04\n"
        ".word 0xe59d0100\n"
        ".word 0xee200a28\n"
        ".word 0xee211a28\n"
        ".word 0xee600aa8\n"
        ".word 0xee611aa8\n"
        ".word 0xeebc0ac0\n"
        ".word 0xeefc0ae0\n"
        ".word 0xee101a10\n"
        ".word 0xeebc0ac1\n"
        ".word 0xee102a90\n"
        ".word 0xe1a01c01\n"
        ".word 0xe20220ff\n"
        ".word 0xe1811802\n"
        ".word 0xee103a10\n"
        ".word 0xeebc0ae1\n"
        ".word 0xe20330ff\n"
        ".word 0xe1811403\n"
        ".word 0xee10ca10\n"
        ".word 0xe20cc0ff\n"
        ".word 0xe181100c\n"
        ".word 0xe6bfcf31\n"
        ".word 0xe6bf2f31\n"
        ".word 0xe6bf3f31\n"
        ".word 0xe1a0cc2c\n"
        ".word 0xe1a02822\n"
        ".word 0xe5c0c000\n"
        ".word 0xe5c02001\n"
        ".word 0xe6bf1f31\n"
        ".word 0xe1a03423\n"
        ".word 0xe28d2c01\n"
        ".word 0xe5c03002\n"
        ".word 0xe5c01003\n"
        ".word 0xe8920003\n"
        ".word 0xe0800001\n"
        ".word 0xe58d0100\n"
        ".word 0xedd40a07\n"
        ".word 0xed9d0a30\n"
        ".word 0xee300a80\n"
        ".word 0xee100a10\n"
        ".word 0xe1500008\n"
        ".word 0xda0000d1\n"
        ".word 0xee100a10\n"
        ".word 0xe1500008\n"
        ".word 0xcef00a6f\n"
        ".word 0xda0000d8\n"
        ".word 0xee300a60\n"
        ".word 0xee100a10\n"
        ".word 0xe1500008\n"
        ".word 0xcafffffb\n"
        ".word 0xea0000d3\n"
        ".word 0x40c90fdb\n"
        ".word 0x3b808081\n"
        ".word 0x437f0000\n"
        ".word 0xe3550000\n"
        ".word 0xe3a06000\n"
        ".word 0xdafffed0\n"
        ".word 0xe51f87a0\n"
        ".word 0xed1f9a09\n"
        ".word 0xed1f8a09\n"
        ".word 0xed5f8a09\n"
        ".word 0xe5941010\n"
        ".word 0xe3510000\n"
        ".word 0xba0000b6\n"
        ".word 0xe59d000c\n"
        ".word 0xebffb9b8\n"
        ".word 0xe59d000c\n"
        ".word 0xe28d10b0\n"
        ".word 0xebffb942\n"
        ".word 0xe51f27d4\n"
        ".word 0xe59dc020\n"
        ".word 0xe59db0c8\n"
        ".word 0xe282ac01\n"
        ".word 0xe58da008\n"
        ".word 0xe2823e11\n"
        ".word 0xe2821e11\n"
        ".word 0xe2820c01\n"
        ".word 0xe282ec01\n"
        ".word 0xe58cb000\n"
        ".word 0xe59d2020\n"
        ".word 0xe59dc0cc\n"
        ".word 0xe28da020\n"
        ".word 0xe582c004\n"
        ".word 0xe59d2020\n"
        ".word 0xe59dc0d0\n"
        ".word 0xe582c008\n"
        ".word 0xe59d2020\n"
        ".word 0xe59dc0d4\n"
        ".word 0xe582c00c\n"
        ".word 0xe89a1004\n"
        ".word 0xe28da090\n"
        ".word 0xe082200c\n"
        ".word 0xe58d2020\n"
        ".word 0xe59d2090\n"
        ".word 0xe594c000\n"
        ".word 0xe582c000\n"
        ".word 0xe59d2090\n"
        ".word 0xe594c004\n"
        ".word 0xe582c004\n"
        ".word 0xe59d2090\n"
        ".word 0xe594c008\n"
        ".word 0xe582c008\n"
        ".word 0xe89a1004\n"
        ".word 0xe082200c\n"
        ".word 0xe58d2090\n"
        ".word 0xe5942014\n"
        ".word 0xe1a0a402\n"
        ".word 0xe1a0b802\n"
        ".word 0xe1a0cc22\n"
        ".word 0xe20220ff\n"
        ".word 0xee012a90\n"
        ".word 0xe1a0ac2a\n"
        ".word 0xe1a0bc2b\n"
        ".word 0xee00ca10\n"
        ".word 0xee00aa90\n"
        ".word 0xee01ba10\n"
        ".word 0xeef81a61\n"
        ".word 0xeeb80a40\n"
        ".word 0xeef80a60\n"
        ".word 0xeeb81a41\n"
        ".word 0xee611a88\n"
        ".word 0xee200a08\n"
        ".word 0xee600a88\n"
        ".word 0xee211a08\n"
        ".word 0xec830a04\n"
        ".word 0xe59d20dc\n"
        ".word 0xe1a03402\n"
        ".word 0xe1a0a802\n"
        ".word 0xe1a0cc23\n"
        ".word 0xe1a03c22\n"
        ".word 0xee003a10\n"
        ".word 0xee01ca90\n"
        ".word 0xe1a0ac2a\n"
        ".word 0xe20220ff\n"
        ".word 0xee00aa90\n"
        ".word 0xee012a10\n"
        ".word 0xeef82a40\n"
        ".word 0xeeb80a61\n"
        ".word 0xeef81a60\n"
        ".word 0xeeb82a41\n"
        ".word 0xee221a88\n"
        ".word 0xee600a08\n"
        ".word 0xee611a88\n"
        ".word 0xee220a08\n"
        ".word 0xe59da008\n"
        ".word 0xed8a1a00\n"
        ".word 0xedca0a01\n"
        ".word 0xedca1a02\n"
        ".word 0xed8a0a03\n"
        ".word 0xed900a00\n"
        ".word 0xedd10a00\n"
        ".word 0xee200a20\n"
        ".word 0xed800a00\n"
        ".word 0xed900a01\n"
        ".word 0xedd10a01\n"
        ".word 0xee200a20\n"
        ".word 0xed800a01\n"
        ".word 0xed900a02\n"
        ".word 0xedd10a02\n"
        ".word 0xee200a20\n"
        ".word 0xed800a02\n"
        ".word 0xedd10a03\n"
        ".word 0xed900a03\n"
        ".word 0xee200a20\n"
        ".word 0xed800a03\n"
        ".word 0xed9e1a00\n"
        ".word 0xedde0a01\n"
        ".word 0xed9e0a02\n"
        ".word 0xee211a28\n"
        ".word 0xee202aa8\n"
        ".word 0xee602a28\n"
        ".word 0xedde1a03\n"
        ".word 0xe59d1100\n"
        ".word 0xee611aa8\n"
        ".word 0xeefc0ac1\n"
        ".word 0xeebc0ac2\n"
        ".word 0xee100a90\n"
        ".word 0xeefc0ae2\n"
        ".word 0xee103a10\n"
        ".word 0xeebc0ae1\n"
        ".word 0xe1a00c00\n"
        ".word 0xe203c0ff\n"
        ".word 0xe180080c\n"
        ".word 0xee102a90\n"
        ".word 0xe20230ff\n"
        ".word 0xee102a10\n"
        ".word 0xe1800403\n"
        ".word 0xe20220ff\n"
        ".word 0xe1800002\n"
        ".word 0xe6bf2f30\n"
        ".word 0xe6bf3f30\n"
        ".word 0xe6bfcf30\n"
        ".word 0xe1a02c22\n"
        ".word 0xe5c12000\n"
        ".word 0xe1a03823\n"
        ".word 0xe6bf0f30\n"
        ".word 0xe1a0c42c\n"
        ".word 0xe5c13001\n"
        ".word 0xe28d2c01\n"
        ".word 0xe5c1c002\n"
        ".word 0xe5c10003\n"
        ".word 0xe8920003\n"
        ".word 0xe0800001\n"
        ".word 0xe58d0100\n"
        ".word 0xedd40a07\n"
        ".word 0xed9d0a30\n"
        ".word 0xee300a80\n"
        ".word 0xee100a10\n"
        ".word 0xe1500008\n"
        ".word 0xda000007\n"
        ".word 0xee100a10\n"
        ".word 0xe1500008\n"
        ".word 0xda00000e\n"
        ".word 0xee300a49\n"
        ".word 0xee100a10\n"
        ".word 0xe1500008\n"
        ".word 0xcafffffb\n"
        ".word 0xea000009\n"
        ".word 0xe59f0498\n"
        ".word 0xee101a10\n"
        ".word 0xe1510000\n"
        ".word 0x8e101a10\n"
        ".word 0x81510000\n"
        ".word 0x9a000003\n"
        ".word 0xee300a09\n"
        ".word 0xee101a10\n"
        ".word 0xe1510000\n"
        ".word 0x8afffffb\n"
        ".word 0xe59d0088\n"
        ".word 0xe2877001\n"
        ".word 0xed800a00\n"
        ".word 0xe1cd08d8\n"
        ".word 0xe0800001\n"
        ".word 0xe58d0088\n"
        ".word 0xed940a06\n"
        ".word 0xeddd0a2e\n"
        ".word 0xe59d0080\n"
        ".word 0xee200a0a\n"
        ".word 0xee600a80\n"
        ".word 0xedc00a00\n"
        ".word 0xeddd0a2f\n"
        ".word 0xe59d0080\n"
        ".word 0xee200a80\n"
        ".word 0xed800a01\n"
        ".word 0xe1cd08d0\n"
        ".word 0xe0800001\n"
        ".word 0xe58d0080\n"
        ".word 0xe2866001\n"
        ".word 0xe1560005\n"
        ".word 0xe2844028\n"
        ".word 0xbaffff41\n"
        ".word 0xea000021\n"
        ".word 0xe59f1410\n"
        ".word 0xee100a10\n"
        ".word 0xe1500001\n"
        ".word 0x8e100a10\n"
        ".word 0x81500001\n"
        ".word 0x8ef00a6f\n"
        ".word 0x9a000003\n"
        ".word 0xee300a20\n"
        ".word 0xee100a10\n"
        ".word 0xe1500001\n"
        ".word 0x8afffffb\n"
        ".word 0xe59d1088\n"
        ".word 0xe2877001\n"
        ".word 0xed810a00\n"
        ".word 0xe1cd08d8\n"
        ".word 0xe0800001\n"
        ".word 0xe58d0088\n"
        ".word 0xed940a06\n"
        ".word 0xeddd0a2e\n"
        ".word 0xe59d0080\n"
        ".word 0xee200a0a\n"
        ".word 0xee600a80\n"
        ".word 0xedc00a00\n"
        ".word 0xeddd0a2f\n"
        ".word 0xe59d0080\n"
        ".word 0xee200a80\n"
        ".word 0xed800a01\n"
        ".word 0xe1cd08d0\n"
        ".word 0xe0800001\n"
        ".word 0xe58d0080\n"
        ".word 0xe2866001\n"
        ".word 0xe1560005\n"
        ".word 0xe2844028\n"
        ".word 0xbafffe44\n"
        ".word 0xe3570000\n"
        ".word 0x0afffde9\n"
        ".word 0xe5990004\n"
        ".word 0xe3c9c0ff\n"
        ".word 0xe6bf2f30\n"
        ".word 0xe6bf3f30\n"
        ".word 0xe6bf4f30\n"
        ".word 0xe6bf1f30\n"
        ".word 0xe1a00c22\n"
        ".word 0xe1a02824\n"
        ".word 0xe180000c\n"
        ".word 0xe1a02402\n"
        ".word 0xe1a03423\n"
        ".word 0xe2022cff\n"
        ".word 0xe3c00cff\n"
        ".word 0xe1800002\n"
        ".word 0xe1a03803\n"
        ".word 0xe20328ff\n"
        ".word 0xe3c008ff\n"
        ".word 0xe1800002\n"
        ".word 0xe3c004ff\n"
        ".word 0xe1800c01\n"
        ".word 0xe59d102c\n"
        ".word 0xe5810064\n"
        ".word 0xe59d002c\n"
        ".word 0xe5807060\n"
        ".word 0xe59d0018\n"
        ".word 0xe5900054\n"
        ".word 0xe6ff0070\n"
        ".word 0xebffb953\n"
        ".word 0xe59d0018\n"
        ".word 0xe5901054\n"
        ".word 0xe5990050\n"
        ".word 0xe6ff1071\n"
        ".word 0xebffb76b\n"
        ".word 0xe28ddf43\n"
        ".word 0xecbd8b10\n"
        ".word 0xe8bd8ff0\n"
        ".word 0xe5996034\n"
        ".word 0xe3550000\n"
        ".word 0xe3a07000\n"
        ".word 0xdafffdc1\n"
        ".word 0xe51fabe0\n"
        ".word 0xed9faab8\n"
        ".word 0xeddfaab8\n"
        ".word 0xe5940010\n"
        ".word 0xe3500000\n"
        ".word 0xba000046\n"
        ".word 0xe5940014\n"
        ".word 0xe28a1c01\n"
        ".word 0xe28ace11\n"
        ".word 0xe28a9e11\n"
        ".word 0xe1a03400\n"
        ".word 0xe28a8c01\n"
        ".word 0xe1a03c23\n"
        ".word 0xee003a10\n"
        ".word 0xe1a03800\n"
        ".word 0xe1a02001\n"
        ".word 0xe1a03c23\n"
        ".word 0xee013a10\n"
        ".word 0xe1a03c20\n"
        ".word 0xeef81a40\n"
        ".word 0xee003a10\n"
        ".word 0xe20000ff\n"
        ".word 0xeeb81a41\n"
        ".word 0xeef80a40\n"
        ".word 0xee210a8a\n"
        ".word 0xee010a90\n"
        ".word 0xe2810008\n"
        ".word 0xee211a0a\n"
        ".word 0xeef81a61\n"
        ".word 0xee600a8a\n"
        ".word 0xee611a8a\n"
        ".word 0xedc10a00\n"
        ".word 0xed810a01\n"
        ".word 0xec801a02\n"
        ".word 0xec8c8a04\n"
        ".word 0xed980a00\n"
        ".word 0xedd90a00\n"
        ".word 0xee200a20\n"
        ".word 0xed880a00\n"
        ".word 0xed980a01\n"
        ".word 0xedd90a01\n"
        ".word 0xee200a20\n"
        ".word 0xed880a01\n"
        ".word 0xed980a02\n"
        ".word 0xedd90a02\n"
        ".word 0xee200a20\n"
        ".word 0xed880a02\n"
        ".word 0xedd90a03\n"
        ".word 0xed980a03\n"
        ".word 0xee200a20\n"
        ".word 0xed880a03\n"
        ".word 0xed910a03\n"
        ".word 0xecd20a03\n"
        ".word 0xee202a2a\n"
        ".word 0xee600aaa\n"
        ".word 0xee611aaa\n"
        ".word 0xee211a2a\n"
        ".word 0xeebc0ae0\n"
        ".word 0xeefc0ac1\n"
        ".word 0xee100a10\n"
        ".word 0xeebc0ae1\n"
        ".word 0xee101a90\n"
        ".word 0xe1a00c00\n"
        ".word 0xe20130ff\n"
        ".word 0xe1800803\n"
        ".word 0xee102a10\n"
        ".word 0xeebc0ac2\n"
        ".word 0xe20220ff\n"
        ".word 0xe1800402\n"
        ".word 0xee101a10\n"
        ".word 0xe20110ff\n"
        ".word 0xe1811000\n"
        ".word 0xe5960000\n"
        ".word 0xebfde236\n"
        ".word 0xe5960000\n"
        ".word 0xe320f000\n"
        ".word 0xebff8d4c\n"
        ".word 0xe2877001\n"
        ".word 0xe1570005\n"
        ".word 0xe2844028\n"
        ".word 0xe2866004\n"
        ".word 0xbaffffb0\n"
        ".word 0xe28ddf43\n"
        ".word 0xecbd8b10\n"
        ".word 0xe8bd8ff0\n"
        ".word 0xe599603c\n"
        ".word 0xe3550000\n"
        ".word 0xe3a07000\n"
        ".word 0xdafffd68\n"
        ".word 0xe51fad44\n"
        ".word 0xed9faa5f\n"
        ".word 0xeddfaa5f\n"
        ".word 0xe5940010\n"
        ".word 0xe3500000\n"
        ".word 0xba000048\n"
        ".word 0xe5940014\n"
        ".word 0xe28a1c01\n"
        ".word 0xe28ace11\n"
        ".word 0xe28a9e11\n"
        ".word 0xe1a03400\n"
        ".word 0xe28a8c01\n"
        ".word 0xe1a03c23\n"
        ".word 0xee003a10\n"
        ".word 0xe1a03800\n"
        ".word 0xe1a02001\n"
        ".word 0xe1a03c23\n"
        ".word 0xeef81a40\n"
        ".word 0xee003a10\n"
        ".word 0xe1a03c20\n"
        ".word 0xee003a90\n"
        ".word 0xe20000ff\n"
        ".word 0xee020a10\n"
        ".word 0xeeb80a40\n"
        ".word 0xeeb81a60\n"
        ".word 0xee610a8a\n"
        ".word 0xee601a0a\n"
        ".word 0xeeb80a42\n"
        ".word 0xee211a0a\n"
        ".word 0xee200a0a\n"
        ".word 0xed811a00\n"
        ".word 0xedc10a01\n"
        ".word 0xedc11a02\n"
        ".word 0xed810a03\n"
        ".word 0xec8c8a04\n"
        ".word 0xed980a00\n"
        ".word 0xedd90a00\n"
        ".word 0xee200a20\n"
        ".word 0xed880a00\n"
        ".word 0xed980a01\n"
        ".word 0xedd90a01\n"
        ".word 0xee200a20\n"
        ".word 0xed880a01\n"
        ".word 0xed980a02\n"
        ".word 0xedd90a02\n"
        ".word 0xee200a20\n"
        ".word 0xed880a02\n"
        ".word 0xedd90a03\n"
        ".word 0xed980a03\n"
        ".word 0xee200a20\n"
        ".word 0xed880a03\n"
        ".word 0xedd21a00\n"
        ".word 0xed920a02\n"
        ".word 0xedd20a01\n"
        ".word 0xee611aaa\n"
        ".word 0xee202a2a\n"
        ".word 0xee600aaa\n"
        ".word 0xed911a03\n"
        ".word 0xee211a2a\n"
        ".word 0xeebc0ae1\n"
        ".word 0xeefc0ae0\n"
        ".word 0xee102a10\n"
        ".word 0xeebc0ac2\n"
        ".word 0xee101a90\n"
        ".word 0xe1a02c02\n"
        ".word 0xe20130ff\n"
        ".word 0xe1822803\n"
        ".word 0xee100a10\n"
        ".word 0xeebc0ac1\n"
        ".word 0xe20010ff\n"
        ".word 0xee100a10\n"
        ".word 0xe20030ff\n"
        ".word 0xe1820401\n"
        ".word 0xe1831000\n"
        ".word 0xe5960000\n"
        ".word 0xeb00e992\n"
        ".word 0xe5960000\n"
        ".word 0xe320f000\n"
        ".word 0xeb00624f\n"
        ".word 0xe2877001\n"
        ".word 0xe1570005\n"
        ".word 0xe2844028\n"
        ".word 0xe2866004\n"
        ".word 0xbaffffae\n"
        ".word 0xe28ddf43\n"
        ".word 0xecbd8b10\n"
        ".word 0xe8bd8ff0\n"
        ".word 0xe5980020\n"
        ".word 0xe5900054\n"
        ".word 0xe6ff0070\n"
        ".word 0xebffb893\n"
        ".word 0xe1a00009\n"
        ".word 0xe320f000\n"
        ".word 0xeb017aba\n"
        ".word 0xe28ddf43\n"
        ".word 0xecbd8b10\n"
        ".word 0xe8bd8ff0\n"
        ".word 0xc0490fdb\n"
        ".word 0x3b808081\n"
        ".word 0x437f0000\n"
    );
}
#if 0
// Original partial readable draft retained for reconstruction; not compiled.
void ui_func_00267fb0(UiPartRenderContext* ctx, f32 scale) {
    UiPartSet* parts = ctx->parts;                       // 0x00267FC4

    // Input colour -> float quad.  The store lands at 0x004EA81C + 0x100,
    // which is exactly 0x004EA91C (`vstmia r0,{s16,s17,s18,s19}`, 0x0026801C).
    f32 tint[4];
    UnpackColor(ctx->color, tint);
    for (s32 i = 0; i < 4; ++i) {
        g_UiPartRenderState.vector[i] = tint[i];
    }

    if (parts->count == 0 || parts->field_10 == 0) {     // 0x00268020..0x00268030
        return;
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
                *reinterpret_cast<u32*>(resource + 0x64) =
                    ByteSwap32(ctx->color);              // 0x00268E5C..0x00268EA8
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
        *reinterpret_cast<u32*>(resource + 0x64) =
            ByteSwap32(ctx->color);                      // 0x00268E5C..0x00268EA8
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
#endif

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
    u8  has_name;                   // +0x06: `ldrb r0,[sp,#0xe]` (0x00198A18)
    u8  pad_07;
    u32 field_08;                   // +0x08: `ldr r1,[sp,#0x10]` (0x001989F8)
    u8  pad_0c[0x14];
};
static_assert(offsetof(QuestRewardEntry, item_id) == 0x04);
static_assert(offsetof(QuestRewardEntry, has_name) == 0x06);
static_assert(offsetof(QuestRewardEntry, field_08) == 0x08);
static_assert(sizeof(QuestRewardEntry) == 0x20);

constexpr const char* kQuestSeparator = "\x81\x7C \x81\x7C \x81\x7C";
constexpr const char* kQuestDash      = "\x81\x7C\x81\x7C\x81\x7C";
constexpr const char* kQuestNoData    = "\x83\x66\x81\x5B\x83\x5E\x96\xB3\x82\xB5x%d";
constexpr const char* kQuestMacca     = "%s\x81\x40\x82\x6D\x82\x8F\x82\x8E\x82\x85";
constexpr const char* kQuestRewardFmt = "%s\x81\x40%s\x81\x5F%s";

} // namespace

// DECOMP_FUNC(0x00197d2c, 4432)
__attribute__((naked)) void ui_func_00197d2c() {
    asm volatile(
        ".word 0xe92d4ff0\n"
        ".word 0xed2d8b06\n"
        ".word 0xe24ddf51\n"
        ".word 0xe59f03a0\n"
        ".word 0xed9faae6\n"
        ".word 0xe59fa39c\n"
        ".word 0xeeb00a4a\n"
        ".word 0xe5904000\n"
        ".word 0xe59a0000\n"
        ".word 0xeb0489c5\n"
        ".word 0xe2840034\n"
        ".word 0xeb049c87\n"
        ".word 0xe1a09000\n"
        ".word 0xe2840034\n"
        ".word 0xeb049c81\n"
        ".word 0xe1a06000\n"
        ".word 0xe2840c05\n"
        ".word 0xe58d00f8\n"
        ".word 0xe5d405c4\n"
        ".word 0xe3500000\n"
        ".word 0x12847b01\n"
        ".word 0x12845b01\n"
        ".word 0x12877f7f\n"
        ".word 0x12855fb1\n"
        ".word 0x02847e66\n"
        ".word 0x02845c07\n"
        ".word 0x0285508a\n"
        ".word 0xe1a00007\n"
        ".word 0xeb041d2f\n"
        ".word 0xe1a08000\n"
        ".word 0xe1a00007\n"
        ".word 0xeb041d26\n"
        ".word 0xe59d10f8\n"
        ".word 0xe0800008\n"
        ".word 0xe0850080\n"
        ".word 0xe5d110f2\n"
        ".word 0xe1d000b0\n"
        ".word 0xe3510000\n"
        ".word 0xe58d0098\n"
        ".word 0x0a000002\n"
        ".word 0xe59f0314\n"
        ".word 0xe19000b4\n"
        ".word 0xe58d0098\n"
        ".word 0xeddfaac3\n"
        ".word 0xe59a0000\n"
        ".word 0xeeb00a6a\n"
        ".word 0xeb0489a0\n"
        ".word 0xeebd0ac0\n"
        ".word 0xe5941004\n"
        ".word 0xe1a05009\n"
        ".word 0xe1a00006\n"
        ".word 0xe3510017\n"
        ".word 0x13510018\n"
        ".word 0x13510019\n"
        ".word 0xee107a10\n"
        ".word 0x1a000007\n"
        ".word 0xe2840b01\n"
        ".word 0xe2800094\n"
        ".word 0xe1a08000\n"
        ".word 0xeb049c57\n"
        ".word 0xe0805009\n"
        ".word 0xe1a00008\n"
        ".word 0xeb049c51\n"
        ".word 0xe0800006\n"
        ".word 0xe3a08065\n"
        ".word 0xe3a02002\n"
        ".word 0xe88d0101\n"
        ".word 0xe0853007\n"
        ".word 0xe3a01029\n"
        ".word 0xe1a00002\n"
        ".word 0xeb049dc3\n"
        ".word 0xeddf9aa8\n"
        ".word 0xe59f5290\n"
        ".word 0xeeb00a69\n"
        ".word 0xe5950000\n"
        ".word 0xeb048983\n"
        ".word 0xeebd0ac0\n"
        ".word 0xe3a02001\n"
        ".word 0xe3a01029\n"
        ".word 0xe88d0140\n"
        ".word 0xee100a10\n"
        ".word 0xe0893000\n"
        ".word 0xe3a00002\n"
        ".word 0xeb049db6\n"
        ".word 0xed9f9a9c\n"
        ".word 0xe5950000\n"
        ".word 0xeeb00a49\n"
        ".word 0xeb048977\n"
        ".word 0xeebd0ac0\n"
        ".word 0xe3a02000\n"
        ".word 0xe3a01029\n"
        ".word 0xe88d0140\n"
        ".word 0xee100a10\n"
        ".word 0xe0893000\n"
        ".word 0xe3a00002\n"
        ".word 0xeb049daa\n"
        ".word 0xe59d0098\n"
        ".word 0xeddf8a90\n"
        ".word 0xed9f8a90\n"
        ".word 0xe3500000\n"
        ".word 0x0a00017d\n"
        ".word 0xeb047a0e\n"
        ".word 0xeeb00a49\n"
        ".word 0xe285a000\n"
        ".word 0xe1a07000\n"
        ".word 0xe59a0000\n"
        ".word 0xeb048964\n"
        ".word 0xeebd0ac0\n"
        ".word 0xe59d0098\n"
        ".word 0xee105a10\n"
        ".word 0xeb040474\n"
        ".word 0xe3500000\n"
        ".word 0xe3a00068\n"
        ".word 0xe0893005\n"
        ".word 0xe58d0004\n"
        ".word 0xe58d6000\n"
        ".word 0x0a000006\n"
        ".word 0xe3a02010\n"
        ".word 0xe3a01029\n"
        ".word 0xe3a00002\n"
        ".word 0xeb049d53\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xea000003\n"
        ".word 0xe3a0200f\n"
        ".word 0xe3a01029\n"
        ".word 0xe3a00002\n"
        ".word 0xeb049d4c\n"
        ".word 0xe3a01011\n"
        ".word 0xe3a00029\n"
        ".word 0xeb049de5\n"
        ".word 0xe1d010f8\n"
        ".word 0xe1d000fa\n"
        ".word 0xe0898005\n"
        ".word 0xe0811008\n"
        ".word 0xe0802006\n"
        ".word 0xe59d0098\n"
        ".word 0xe3a0306a\n"
        ".word 0xeb040c01\n"
        ".word 0xe3a01012\n"
        ".word 0xe3a00029\n"
        ".word 0xeb049dda\n"
        ".word 0xe1a05000\n"
        ".word 0xe59d0098\n"
        ".word 0xe3a01000\n"
        ".word 0xeb049415\n"
        ".word 0xe1a02000\n"
        ".word 0xe28f1d06\n"
        ".word 0xe28d0018\n"
        ".word 0xfa049a1d\n"
        ".word 0xe1d500f8\n"
        ".word 0xe1d510fa\n"
        ".word 0xed9f9a5c\n"
        ".word 0xe0800008\n"
        ".word 0xe0811006\n"
        ".word 0xee000a10\n"
        ".word 0xee001a90\n"
        ".word 0xeeb02a48\n"
        ".word 0xeef01a68\n"
        ".word 0xeeb01a49\n"
        ".word 0xe28d2018\n"
        ".word 0xeeb80ac0\n"
        ".word 0xeef80ae0\n"
        ".word 0xe3e01000\n"
        ".word 0xe3a00003\n"
        ".word 0xeb0499ed\n"
        ".word 0xe59f0118\n"
        ".word 0xed9f0a4e\n"
        ".word 0xe5900000\n"
        ".word 0xeb048925\n"
        ".word 0xeebd0ac0\n"
        ".word 0xe5971150\n"
        ".word 0xe3a05000\n"
        ".word 0xe3510000\n"
        ".word 0xee100a10\n"
        ".word 0x9a000015\n"
        ".word 0xe3a0b005\n"
        ".word 0xe3a0a06a\n"
        ".word 0xe0898000\n"
        ".word 0xe0850fa5\n"
        ".word 0xe08b10c0\n"
        ".word 0xe3a00029\n"
        ".word 0xeb049db1\n"
        ".word 0xe1d010fa\n"
        ".word 0xe3150001\n"
        ".word 0xe0811006\n"
        ".word 0xe88d0402\n"
        ".word 0xe1d000f8\n"
        ".word 0xe0803008\n"
        ".word 0x0a00006f\n"
        ".word 0xe3a0200e\n"
        ".word 0xe3a01029\n"
        ".word 0xe3a00002\n"
        ".word 0xeb049d0a\n"
        ".word 0xe5970150\n"
        ".word 0xe2855001\n"
        ".word 0xe1500005\n"
        ".word 0x8affffec\n"
        ".word 0xe59fb098\n"
        ".word 0xeeb00a69\n"
        ".word 0xe59b0000\n"
        ".word 0xeb048905\n"
        ".word 0xeebd0ac0\n"
        ".word 0xe3a0101a\n"
        ".word 0xe3a00029\n"
        ".word 0xee10aa10\n"
        ".word 0xeb049d99\n"
        ".word 0xe1a05000\n"
        ".word 0xe59d0098\n"
        ".word 0xebfe0cbf\n"
        ".word 0xe1a02000\n"
        ".word 0xe28f1080\n"
        ".word 0xe28d0018\n"
        ".word 0xfa0499dd\n"
        ".word 0xe1d500f8\n"
        ".word 0xe1d510fa\n"
        ".word 0xe089800a\n"
        ".word 0xe0800008\n"
        ".word 0xe0811006\n"
        ".word 0xee000a10\n"
        ".word 0xee001a90\n"
        ".word 0xeeb02a48\n"
        ".word 0xeef01a68\n"
        ".word 0xeeb01a49\n"
        ".word 0xe28d2018\n"
        ".word 0xeeb80ac0\n"
        ".word 0xeef80ae0\n"
        ".word 0xe3a010ff\n"
        ".word 0xe3a00002\n"
        ".word 0xeb0499ad\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xeb045790\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xea00000b\n"
        ".word 0x3ea66666\n"
        ".word 0x0043dd50\n"
        ".word 0x0044ea00\n"
        ".word 0x0000097e\n"
        ".word 0x3ea3d70a\n"
        ".word 0x3ea147ae\n"
        ".word 0x3e9eb852\n"
        ".word 0x00000000\n"
        ".word 0x3f800000\n"
        ".word 0x00007325\n"
        ".word 0x3ee66666\n"
        ".word 0x3e9c28f6\n"
        ".word 0xe59d1098\n"
        ".word 0xe0800101\n"
        ".word 0xe5d00200\n"
        ".word 0xe3100008\n"
        ".word 0xe1a01e00\n"
        ".word 0xe1a01fa1\n"
        ".word 0xe0811081\n"
        ".word 0xe0871101\n"
        ".word 0xe2815f55\n"
        ".word 0x0a000002\n"
        ".word 0xe1d500b0\n"
        ".word 0xe3500000\n"
        ".word 0x02875f55\n"
        ".word 0xe1d500b0\n"
        ".word 0xe3500001\n"
        ".word 0x0a00002c\n"
        ".word 0xe3500003\n"
        ".word 0x0a000089\n"
        ".word 0xe3500004\n"
        ".word 0x0a000094\n"
        ".word 0xe28f1fe7\n"
        ".word 0xe28d0018\n"
        ".word 0xfa0499a4\n"
        ".word 0xe3a0101b\n"
        ".word 0xe3a00029\n"
        ".word 0xeb049d56\n"
        ".word 0xe1d010f8\n"
        ".word 0xe1d020fa\n"
        ".word 0xeeb02a48\n"
        ".word 0xe0810008\n"
        ".word 0xe0821006\n"
        ".word 0xee000a10\n"
        ".word 0xee001a90\n"
        ".word 0xeef01a68\n"
        ".word 0xeeb01a49\n"
        ".word 0xe28d2018\n"
        ".word 0xe3e01000\n"
        ".word 0xeeb80ac0\n"
        ".word 0xeef80ae0\n"
        ".word 0xe3a00002\n"
        ".word 0xeb049972\n"
        ".word 0xeeb00a6a\n"
        ".word 0xe59b0000\n"
        ".word 0xeb0488ab\n"
        ".word 0xeebd0ac0\n"
        ".word 0xe5940004\n"
        ".word 0xe1a05006\n"
        ".word 0xe3500017\n"
        ".word 0x13500018\n"
        ".word 0x13500019\n"
        ".word 0xee107a10\n"
        ".word 0xe0898007\n"
        ".word 0x0a00007f\n"
        ".word 0xea00008a\n"
        ".word 0xe3a0200d\n"
        ".word 0xe3a01029\n"
        ".word 0xe3a00002\n"
        ".word 0xeb049c9a\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xeaffff8c\n"
        ".word 0xe1d500b2\n"
        ".word 0xe3500000\n"
        ".word 0x0a000051\n"
        ".word 0xe3a0101b\n"
        ".word 0xe3a00029\n"
        ".word 0xeb049d2d\n"
        ".word 0xe3a01000\n"
        ".word 0xe58d1000\n"
        ".word 0xe1d010f8\n"
        ".word 0xe1d020fa\n"
        ".word 0xe1d500f2\n"
        ".word 0xe0811008\n"
        ".word 0xe0822006\n"
        ".word 0xe3a0306a\n"
        ".word 0xeb0498c2\n"
        ".word 0xe3a0101c\n"
        ".word 0xe3a00029\n"
        ".word 0xeb049d21\n"
        ".word 0xe1a07000\n"
        ".word 0xe1d500b2\n"
        ".word 0xe3a01000\n"
        ".word 0xeb049973\n"
        ".word 0xe1a02000\n"
        ".word 0xe24f1f59\n"
        ".word 0xe28d0018\n"
        ".word 0xfa049964\n"
        ".word 0xe1d700f8\n"
        ".word 0xe1d710fa\n"
        ".word 0xeeb02a48\n"
        ".word 0xe0800008\n"
        ".word 0xe0811006\n"
        ".word 0xee000a10\n"
        ".word 0xee001a90\n"
        ".word 0xeef01a68\n"
        ".word 0xeeb01a49\n"
        ".word 0xe28d2018\n"
        ".word 0xe3e01000\n"
        ".word 0xeeb80ac0\n"
        ".word 0xeef80ae0\n"
        ".word 0xe3a00002\n"
        ".word 0xeb049935\n"
        ".word 0xeeb00a68\n"
        ".word 0xe3a01002\n"
        ".word 0xe28d0018\n"
        ".word 0xeb03dd28\n"
        ".word 0xeddf0a93\n"
        ".word 0xe28f3f93\n"
        ".word 0xe3a0206a\n"
        ".word 0xee300a20\n"
        ".word 0xe3a00007\n"
        ".word 0xe88d000d\n"
        ".word 0xe3a03000\n"
        ".word 0xe1d720f8\n"
        ".word 0xe1d700fa\n"
        ".word 0xeebd0ac0\n"
        ".word 0xee101a10\n"
        ".word 0xe081800a\n"
        ".word 0xe0821009\n"
        ".word 0xe0802006\n"
        ".word 0xe0811008\n"
        ".word 0xe1a00003\n"
        ".word 0xeb04979c\n"
        ".word 0xe1d510b4\n"
        ".word 0xe28d00b0\n"
        ".word 0xeb03e1d8\n"
        ".word 0xe1d710f8\n"
        ".word 0xe1d700fa\n"
        ".word 0xeeb02a48\n"
        ".word 0xe0811009\n"
        ".word 0xe0811008\n"
        ".word 0xe0800006\n"
        ".word 0xe2811007\n"
        ".word 0xee000a90\n"
        ".word 0xee001a10\n"
        ".word 0xeef01a68\n"
        ".word 0xeeb01a49\n"
        ".word 0xe28d20b0\n"
        ".word 0xe3e01000\n"
        ".word 0xeef80ae0\n"
        ".word 0xeeb80ac0\n"
        ".word 0xe3a00002\n"
        ".word 0xeb04990c\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xeaffff96\n"
        ".word 0xe1d520b4\n"
        ".word 0xe28f1e1b\n"
        ".word 0xe28d0018\n"
        ".word 0xfa049925\n"
        ".word 0xe3a0101c\n"
        ".word 0xe3a00029\n"
        ".word 0xeb049cd7\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xeaffff8c\n"
        ".word 0xe1d510b4\n"
        ".word 0xe28d00b0\n"
        ".word 0xeb03e1b7\n"
        ".word 0xe28d20b0\n"
        ".word 0xe28f1f63\n"
        ".word 0xe28d0018\n"
        ".word 0xfa049918\n"
        ".word 0xe3a0101b\n"
        ".word 0xe3a00029\n"
        ".word 0xeb049cca\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xeaffff70\n"
        ".word 0xe1d500b2\n"
        ".word 0xeb066e0b\n"
        ".word 0xe1a02000\n"
        ".word 0xe24f1fb1\n"
        ".word 0xe28d0018\n"
        ".word 0xfa04990c\n"
        ".word 0xe3a0101b\n"
        ".word 0xe3a00029\n"
        ".word 0xeb049cbe\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xeaffff64\n"
        ".word 0xe2840b01\n"
        ".word 0xe2800094\n"
        ".word 0xe1a05000\n"
        ".word 0xeb049ae2\n"
        ".word 0xe0800009\n"
        ".word 0xe0808007\n"
        ".word 0xe1a00005\n"
        ".word 0xeb049adb\n"
        ".word 0xe0805006\n"
        ".word 0xe5940004\n"
        ".word 0xe3500018\n"
        ".word 0x0a00005a\n"
        ".word 0xe5940008\n"
        ".word 0xe3500018\n"
        ".word 0x0a000057\n"
        ".word 0xe3a0006a\n"
        ".word 0xe58d0004\n"
        ".word 0xe1a03008\n"
        ".word 0xe3a02023\n"
        ".word 0xe3a01029\n"
        ".word 0xe3a00002\n"
        ".word 0xe58d5000\n"
        ".word 0xeb049c08\n"
        ".word 0xe3a01025\n"
        ".word 0xe3a00029\n"
        ".word 0xeb049ca1\n"
        ".word 0xe3a0a006\n"
        ".word 0xe3a01000\n"
        ".word 0xe58d1004\n"
        ".word 0xe58da000\n"
        ".word 0xe1d010fa\n"
        ".word 0xe1d030f8\n"
        ".word 0xeeb00a48\n"
        ".word 0xe0812005\n"
        ".word 0xe2847b01\n"
        ".word 0xe0831008\n"
        ".word 0xe59405d8\n"
        ".word 0xe2877f76\n"
        ".word 0xe3a0306f\n"
        ".word 0xeb047d2a\n"
        ".word 0xe3a01026\n"
        ".word 0xe3a00029\n"
        ".word 0xeb049c90\n"
        ".word 0xe3a01001\n"
        ".word 0xe58d1004\n"
        ".word 0xe58da000\n"
        ".word 0xe1d010fa\n"
        ".word 0xe1d030f8\n"
        ".word 0xeeb00a48\n"
        ".word 0xe0812005\n"
        ".word 0xe0831008\n"
        ".word 0xe5970000\n"
        ".word 0xe3a0306f\n"
        ".word 0xeb047d1c\n"
        ".word 0xe51f03dc\n"
        ".word 0xeeb00a4a\n"
        ".word 0xe5900000\n"
        ".word 0xeb0487e8\n"
        ".word 0xeebd0ac0\n"
        ".word 0xe2840f76\n"
        ".word 0xee10aa10\n"
        ".word 0xeb049aa8\n"
        ".word 0xe0800009\n"
        ".word 0xe080800a\n"
        ".word 0xe2840f76\n"
        ".word 0xeb049aa1\n"
        ".word 0xe0807006\n"
        ".word 0xe3a00065\n"
        ".word 0xe1a03008\n"
        ".word 0xe3a02003\n"
        ".word 0xe3a01029\n"
        ".word 0xea00000b\n"
        ".word 0x7c817c81\n"
        ".word 0x00007c81\n"
        ".word 0x40400000\n"
        ".word 0x0000002a\n"
        ".word 0x5b816683\n"
        ".word 0xb3965e83\n"
        ".word 0x2578b582\n"
        ".word 0x00000064\n"
        ".word 0x40817325\n"
        ".word 0x81826c82\n"
        ".word 0x83828382\n"
        ".word 0x00008182\n"
        ".word 0xe58d0004\n"
        ".word 0xe3a00002\n"
        ".word 0xe58d7000\n"
        ".word 0xeb049c05\n"
        ".word 0xe59d0098\n"
        ".word 0xe3500000\n"
        ".word 0x0a000238\n"
        ".word 0xeb04786b\n"
        ".word 0xe1a0b000\n"
        ".word 0xe59d00f8\n"
        ".word 0xe5d000c4\n"
        ".word 0xe3500000\n"
        ".word 0x0a000045\n"
        ".word 0xe59d0098\n"
        ".word 0xeb0402d3\n"
        ".word 0xe3500000\n"
        ".word 0xe320f000\n"
        ".word 0x0a000082\n"
        ".word 0xea000079\n"
        ".word 0xe2840e52\n"
        ".word 0xed900a08\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xeb049c5f\n"
        ".word 0xe59b7000\n"
        ".word 0xe3a02000\n"
        ".word 0xe3a01001\n"
        ".word 0xe3a00006\n"
        ".word 0xeb04b67f\n"
        ".word 0xe2877a01\n"
        ".word 0xe2877fab\n"
        ".word 0xe5971000\n"
        ".word 0xe0872101\n"
        ".word 0xe5921008\n"
        ".word 0xe5820008\n"
        ".word 0xe5d72018\n"
        ".word 0xe3520000\n"
        ".word 0x01510000\n"
        ".word 0x0a000003\n"
        ".word 0xe597101c\n"
        ".word 0xe12fff31\n"
        ".word 0xe3a00000\n"
        ".word 0xe5c70018\n"
        ".word 0xe3a00068\n"
        ".word 0xe58d0004\n"
        ".word 0xe1a03008\n"
        ".word 0xe3a02060\n"
        ".word 0xe3a01029\n"
        ".word 0xe3a00002\n"
        ".word 0xe58d5000\n"
        ".word 0xeb049b98\n"
        ".word 0xe59b7000\n"
        ".word 0xe3a02000\n"
        ".word 0xe3a01007\n"
        ".word 0xe3a00006\n"
        ".word 0xeb04b664\n"
        ".word 0xe2877a01\n"
        ".word 0xe2877fab\n"
        ".word 0xe5971000\n"
        ".word 0xe0872101\n"
        ".word 0xe5921008\n"
        ".word 0xe5820008\n"
        ".word 0xe5d72018\n"
        ".word 0xe3520000\n"
        ".word 0x01510000\n"
        ".word 0x0a000003\n"
        ".word 0xe597101c\n"
        ".word 0xe12fff31\n"
        ".word 0xe3a00000\n"
        ".word 0xe5c70018\n"
        ".word 0xeeb00a48\n"
        ".word 0xeb049c2f\n"
        ".word 0xe3a0006a\n"
        ".word 0xe58d0004\n"
        ".word 0xe1a03008\n"
        ".word 0xe3a02024\n"
        ".word 0xe3a01029\n"
        ".word 0xe3a00002\n"
        ".word 0xe58d5000\n"
        ".word 0xeb049b7b\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xeaffff6f\n"
        ".word 0xe5db0006\n"
        ".word 0xe3500000\n"
        ".word 0xe59d0098\n"
        ".word 0x0a000004\n"
        ".word 0xeb03dbc5\n"
        ".word 0xe3500000\n"
        ".word 0xe320f000\n"
        ".word 0x1a00000b\n"
        ".word 0xea000005\n"
        ".word 0xe320f000\n"
        ".word 0xeb040284\n"
        ".word 0xe3500000\n"
        ".word 0xe320f000\n"
        ".word 0x1a00002b\n"
        ".word 0xea000032\n"
        ".word 0xe320f000\n"
        ".word 0xe3a00000\n"
        ".word 0xe3500000\n"
        ".word 0xe320f000\n"
        ".word 0x0a000020\n"
        ".word 0xe320f000\n"
        ".word 0xeb03dfef\n"
        ".word 0xe1a01000\n"
        ".word 0xe59d0098\n"
        ".word 0xe1510000\n"
        ".word 0x1a000014\n"
        ".word 0xe5940004\n"
        ".word 0xe350000c\n"
        ".word 0x0a00000a\n"
        ".word 0xe3a00068\n"
        ".word 0xe58d0004\n"
        ".word 0xe1a03008\n"
        ".word 0xe3a0202a\n"
        ".word 0xe3a01029\n"
        ".word 0xe3a00002\n"
        ".word 0xe58d7000\n"
        ".word 0xeb049b53\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xea000019\n"
        ".word 0xee00aa10\n"
        ".word 0xe2840f99\n"
        ".word 0xeeb80ac0\n"
        ".word 0xeb0483f6\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xea000012\n"
        ".word 0xe320f000\n"
        ".word 0xeb04025e\n"
        ".word 0xe3500000\n"
        ".word 0xe320f000\n"
        ".word 0x0a00000d\n"
        ".word 0xea000004\n"
        ".word 0xe59d0098\n"
        ".word 0xeb040258\n"
        ".word 0xe3500000\n"
        ".word 0xe320f000\n"
        ".word 0x0a000007\n"
        ".word 0xe3a00068\n"
        ".word 0xe58d0004\n"
        ".word 0xe1a03008\n"
        ".word 0xe3a0202b\n"
        ".word 0xe3a01029\n"
        ".word 0xe3a00002\n"
        ".word 0xe58d7000\n"
        ".word 0xeb049b36\n"
        ".word 0xe59405d0\n"
        ".word 0xe3a05000\n"
        ".word 0xe3500000\n"
        ".word 0xc089000a\n"
        ".word 0xc58d000c\n"
        ".word 0xda00001c\n"
        ".word 0xe59405c8\n"
        ".word 0xe1500005\n"
        ".word 0x0a000015\n"
        ".word 0xe2851048\n"
        ".word 0xe3a00029\n"
        ".word 0xeb049bc6\n"
        ".word 0xe1a0a000\n"
        ".word 0xe1d000fa\n"
        ".word 0xe3a01065\n"
        ".word 0xe3a02040\n"
        ".word 0xe0800006\n"
        ".word 0xe1cd00f0\n"
        ".word 0xe1da00f8\n"
        ".word 0xe59d100c\n"
        ".word 0xe0803001\n"
        ".word 0xe3a01029\n"
        ".word 0xe3a00002\n"
        ".word 0xeb049b1e\n"
        ".word 0xe3550000\n"
        ".word 0xe320f000\n"
        ".word 0x0a00000d\n"
        ".word 0xe3550001\n"
        ".word 0x0a000019\n"
        ".word 0xe3550002\n"
        ".word 0x0a000028\n"
        ".word 0xe59405d0\n"
        ".word 0xe2855001\n"
        ".word 0xe1500005\n"
        ".word 0xcaffffe2\n"
        ".word 0xe59405c8\n"
        ".word 0xe3500000\n"
        ".word 0x03a05000\n"
        ".word 0x03a0a006\n"
        ".word 0x0a00002d\n"
        ".word 0xea00005d\n"
        ".word 0xe1da00fa\n"
        ".word 0xe3a0106a\n"
        ".word 0xe3a02041\n"
        ".word 0xe0800006\n"
        ".word 0xe1cd00f0\n"
        ".word 0xe1da00f8\n"
        ".word 0xe59d100c\n"
        ".word 0xe0803001\n"
        ".word 0xe3a01029\n"
        ".word 0xe3a00002\n"
        ".word 0xeb049b02\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xeaffffe7\n"
        ".word 0xe5db0007\n"
        ".word 0xe3100040\n"
        ".word 0x0a00000d\n"
        ".word 0xe1da00fa\n"
        ".word 0xe3a0106a\n"
        ".word 0xe3a02042\n"
        ".word 0xe0800006\n"
        ".word 0xe1cd00f0\n"
        ".word 0xe1da10f8\n"
        ".word 0xe59d000c\n"
        ".word 0xe0813000\n"
        ".word 0xe3a01029\n"
        ".word 0xe3a00002\n"
        ".word 0xeb049af1\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xeaffffd6\n"
        ".word 0xe1da00fa\n"
        ".word 0xe3a0106a\n"
        ".word 0xe3a02043\n"
        ".word 0xe0800006\n"
        ".word 0xe1cd00f0\n"
        ".word 0xe1da10f8\n"
        ".word 0xe59d000c\n"
        ".word 0xe0813000\n"
        ".word 0xe3a01029\n"
        ".word 0xe3a00002\n"
        ".word 0xeb049ae3\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xeaffffc8\n"
        ".word 0xe3a01034\n"
        ".word 0xe3a00029\n"
        ".word 0xeb049b79\n"
        ".word 0xe58d5004\n"
        ".word 0xe58da000\n"
        ".word 0xe1d020fa\n"
        ".word 0xe1d030f8\n"
        ".word 0xe0851205\n"
        ".word 0xe0811007\n"
        ".word 0xe0822001\n"
        ".word 0xeeb00a48\n"
        ".word 0xe0831008\n"
        ".word 0xe59405d4\n"
        ".word 0xe3a0306f\n"
        ".word 0xeb047c04\n"
        ".word 0xe2855001\n"
        ".word 0xe3550007\n"
        ".word 0xbaffffed\n"
        ".word 0xe51f0848\n"
        ".word 0xeeb00a6a\n"
        ".word 0xe5900000\n"
        ".word 0xeb0486cd\n"
        ".word 0xeebd0ac0\n"
        ".word 0xe3a01048\n"
        ".word 0xe3a00029\n"
        ".word 0xee10aa10\n"
        ".word 0xeb049b61\n"
        ".word 0xe1a05000\n"
        ".word 0xe1d000fa\n"
        ".word 0xe3a0106f\n"
        ".word 0xe08aa009\n"
        ".word 0xe0800006\n"
        ".word 0xe1cd00f0\n"
        ".word 0xe1d500f8\n"
        ".word 0xe3a02044\n"
        ".word 0xe3a01029\n"
        ".word 0xe080300a\n"
        ".word 0xe3a00002\n"
        ".word 0xeb049ab9\n"
        ".word 0xe1d500fa\n"
        ".word 0xe3a01074\n"
        ".word 0xe3a02045\n"
        ".word 0xe0800006\n"
        ".word 0xe1cd00f0\n"
        ".word 0xe1d500f8\n"
        ".word 0xe3a01029\n"
        ".word 0xe080300a\n"
        ".word 0xe3a00002\n"
        ".word 0xeb049aaf\n"
        ".word 0xe59405c8\n"
        ".word 0xe3500001\n"
        ".word 0x1a0000bb\n"
        ".word 0xe5db0007\n"
        ".word 0xe3100040\n"
        ".word 0x0a0000c8\n"
        ".word 0xe3a00001\n"
        ".word 0xe3a0a000\n"
        ".word 0xed9f9abb\n"
        ".word 0xe1a0500a\n"
        ".word 0xe58d0138\n"
        ".word 0xe59d0098\n"
        ".word 0xe28d2008\n"
        ".word 0xe1a01005\n"
        ".word 0xeb0401bf\n"
        ".word 0xe3500000\n"
        ".word 0xe320f000\n"
        ".word 0x0a00003d\n"
        ".word 0xe3a01034\n"
        ".word 0xe3a00029\n"
        ".word 0xeb049b36\n"
        ".word 0xe58d00f0\n"
        ".word 0xe59d1010\n"
        ".word 0xe28d0f46\n"
        ".word 0xeb03e018\n"
        ".word 0xe08b0185\n"
        ".word 0xe58d0014\n"
        ".word 0xe5901170\n"
        ".word 0xe28d00f8\n"
        ".word 0xeb03e013\n"
        ".word 0xe5dd000e\n"
        ".word 0xe3500000\n"
        ".word 0xe1dd00bc\n"
        ".word 0x0a00000b\n"
        ".word 0xe3a01000\n"
        ".word 0xeb04977d\n"
        ".word 0xe28d10f8\n"
        ".word 0xe1a02000\n"
        ".word 0xe58d1000\n"
        ".word 0xe28d3f46\n"
        ".word 0xe28f1e27\n"
        ".word 0xe28d0018\n"
        ".word 0xfa04976b\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xea000008\n"
        ".word 0xe320f000\n"
        ".word 0xeb0491fd\n"
        ".word 0xe28d10f8\n"
        ".word 0xe1a02000\n"
        ".word 0xe58d1000\n"
        ".word 0xe28d3f46\n"
        ".word 0xe28f1d09\n"
        ".word 0xe28d0018\n"
        ".word 0xfa04975f\n"
        ".word 0xe59d0014\n"
        ".word 0xe59d1010\n"
        ".word 0xe0852205\n"
        ".word 0xe0822007\n"
        ".word 0xe5900170\n"
        ".word 0xeeb02a48\n"
        ".word 0xeef01a68\n"
        ".word 0xe1510000\n"
        ".word 0x33a00000\n"
        ".word 0x358d0138\n"
        ".word 0xe59d00f0\n"
        ".word 0xeeb01a49\n"
        ".word 0xe1d010fa\n"
        ".word 0xe1d000f8\n"
        ".word 0xe0811002\n"
        ".word 0xe0800008\n"
        ".word 0xee001a90\n"
        ".word 0xee000a10\n"
        ".word 0xe59f11f8\n"
        ".word 0xe28d2018\n"
        ".word 0xe3a00003\n"
        ".word 0xeef80ae0\n"
        ".word 0xeeb80ac0\n"
        ".word 0xeb049727\n"
        ".word 0xe28aa001\n"
        ".word 0xe2855001\n"
        ".word 0xe3550006\n"
        ".word 0xbaffffb7\n"
        ".word 0xe5db0006\n"
        ".word 0xe3500000\n"
        ".word 0x1a000047\n"
        ".word 0xe59d0098\n"
        ".word 0xeb040160\n"
        ".word 0xe3500000\n"
        ".word 0xe320f000\n"
        ".word 0x0a000004\n"
        ".word 0xe59d0098\n"
        ".word 0xeb03da52\n"
        ".word 0xe3500000\n"
        ".word 0x03a00000\n"
        ".word 0x058d0138\n"
        ".word 0xe5db0006\n"
        ".word 0xe3500000\n"
        ".word 0x1a00003a\n"
        ".word 0xe59d0138\n"
        ".word 0xe3500000\n"
        ".word 0x0a000037\n"
        ".word 0xe3a01034\n"
        ".word 0xe3a00029\n"
        ".word 0xeb049ae2\n"
        ".word 0xe58d00f0\n"
        ".word 0xe59d0098\n"
        ".word 0xeb04014c\n"
        ".word 0xe3500000\n"
        ".word 0xe320f000\n"
        ".word 0x1a00005a\n"
        ".word 0xe3a00f67\n"
        ".word 0xe19000bb\n"
        ".word 0xe3500000\n"
        ".word 0x0a000056\n"
        ".word 0xe3500001\n"
        ".word 0x03a05007\n"
        ".word 0x13a05008\n"
        ".word 0xe3a01000\n"
        ".word 0xe3a00034\n"
        ".word 0xeb04a0cf\n"
        ".word 0xe58d0004\n"
        ".word 0xe320f000\n"
        ".word 0xeb04a0c2\n"
        ".word 0xe58d0014\n"
        ".word 0xe59d0004\n"
        ".word 0xeb04a0ab\n"
        ".word 0xe1550000\n"
        ".word 0xe320f000\n"
        ".word 0x2a00001b\n"
        ".word 0xe0850105\n"
        ".word 0xe0801285\n"
        ".word 0xe59d0014\n"
        ".word 0xe0800081\n"
        ".word 0xe2902001\n"
        ".word 0x0a000015\n"
        ".word 0xe28f10f8\n"
        ".word 0xe28d0018\n"
        ".word 0xfa04970b\n"
        ".word 0xe59d00f0\n"
        ".word 0xe08a220a\n"
        ".word 0xe2822011\n"
        ".word 0xeeb02a48\n"
        ".word 0xe1d010fa\n"
        ".word 0xe1d000f8\n"
        ".word 0xeef01a68\n"
        ".word 0xe0811007\n"
        ".word 0xe0811002\n"
        ".word 0xe0800008\n"
        ".word 0xee001a90\n"
        ".word 0xee000a10\n"
        ".word 0xeeb01a49\n"
        ".word 0xe59f10bc\n"
        ".word 0xe28d2018\n"
        ".word 0xe3a00003\n"
        ".word 0xeef80ae0\n"
        ".word 0xeeb80ac0\n"
        ".word 0xeb0496d8\n"
        ".word 0xe51f0b3c\n"
        ".word 0xeeb00a6a\n"
        ".word 0xe5900000\n"
        ".word 0xeb048610\n"
        ".word 0xeebd0ac0\n"
        ".word 0xe3a01049\n"
        ".word 0xe3a00029\n"
        ".word 0xee10aa10\n"
        ".word 0xeb049aa4\n"
        ".word 0xe1a05000\n"
        ".word 0xe1d000fa\n"
        ".word 0xe08aa009\n"
        ".word 0xe3a02044\n"
        ".word 0xe0801006\n"
        ".word 0xe3a0006f\n"
        ".word 0xe58d0004\n"
        ".word 0xe58d1000\n"
        ".word 0xe1d500f8\n"
        ".word 0xe3a01029\n"
        ".word 0xe080300a\n"
        ".word 0xe3a00002\n"
        ".word 0xeb0499fb\n"
        ".word 0xe1d500fa\n"
        ".word 0xe3a02046\n"
        ".word 0xe0801006\n"
        ".word 0xe3a00074\n"
        ".word 0xe58d0004\n"
        ".word 0xe58d1000\n"
        ".word 0xe1d500f8\n"
        ".word 0xe3a01029\n"
        ".word 0xe080300a\n"
        ".word 0xe3a00002\n"
        ".word 0xeb0499f0\n"
        ".word 0xe59405c8\n"
        ".word 0xe3500002\n"
        ".word 0x0a00000c\n"
        ".word 0xe3500001\n"
        ".word 0x0a000007\n"
        ".word 0xea000041\n"
        ".word 0x3f147ae1\n"
        ".word 0x40817325\n"
        ".word 0x5e817325\n"
        ".word 0x00007325\n"
        ".word 0x320202ff\n"
        ".word 0xe3a05009\n"
        ".word 0xeaffffa9\n"
        ".word 0xe5db0007\n"
        ".word 0xe3100040\n"
        ".word 0x1a000037\n"
        ".word 0xe3a05000\n"
        ".word 0xe3a0a006\n"
        ".word 0xe3a01034\n"
        ".word 0xe3a00029\n"
        ".word 0xeb049a77\n"
        ".word 0xe58d5004\n"
        ".word 0xe58da000\n"
        ".word 0xe1d020fa\n"
        ".word 0xe1d030f8\n"
        ".word 0xe0851205\n"
        ".word 0xe0811007\n"
        ".word 0xe0822001\n"
        ".word 0xeeb00a48\n"
        ".word 0xe0831008\n"
        ".word 0xe59405dc\n"
        ".word 0xe3a0306f\n"
        ".word 0xeb047b02\n"
        ".word 0xe2855001\n"
        ".word 0xe3550007\n"
        ".word 0xbaffffed\n"
        ".word 0xe51f0c50\n"
        ".word 0xeeb00a6a\n"
        ".word 0xe5900000\n"
        ".word 0xeb0485cb\n"
        ".word 0xeebd0ac0\n"
        ".word 0xe59405c8\n"
        ".word 0xe3500002\n"
        ".word 0xee107a10\n"
        ".word 0x0a00003a\n"
        ".word 0xe3a01049\n"
        ".word 0xe3a00029\n"
        ".word 0xeb049a5c\n"
        ".word 0xe1a05000\n"
        ".word 0xe0877009\n"
        ".word 0xe1d500fa\n"
        ".word 0xe3a02044\n"
        ".word 0xe0801006\n"
        ".word 0xe3a0006f\n"
        ".word 0xe58d0004\n"
        ".word 0xe58d1000\n"
        ".word 0xe1d500f8\n"
        ".word 0xe3a01029\n"
        ".word 0xe0803007\n"
        ".word 0xe3a00002\n"
        ".word 0xeb0499b3\n"
        ".word 0xe1d500fa\n"
        ".word 0xe3a02047\n"
        ".word 0xe0801006\n"
        ".word 0xe3a00074\n"
        ".word 0xe58d0004\n"
        ".word 0xe58d1000\n"
        ".word 0xe1d500f8\n"
        ".word 0xe3a01029\n"
        ".word 0xe0803007\n"
        ".word 0xe3a00002\n"
        ".word 0xeb0499a8\n"
        ".word 0xe59405d0\n"
        ".word 0xe3500001\n"
        ".word 0xda000019\n"
        ".word 0xe51f0cec\n"
        ".word 0xeeb00a6a\n"
        ".word 0xe5900000\n"
        ".word 0xeb0485a4\n"
        ".word 0xeebd0ac0\n"
        ".word 0xe5940004\n"
        ".word 0xe3a08004\n"
        ".word 0xe3a05005\n"
        ".word 0xe3500005\n"
        ".word 0x13500004\n"
        ".word 0xee107a10\n"
        ".word 0x0a000016\n"
        ".word 0xe3a0a079\n"
        ".word 0xe0894007\n"
        ".word 0xe1a03004\n"
        ".word 0xe1a02008\n"
        ".word 0xe3a01029\n"
        ".word 0xe3a00002\n"
        ".word 0xe88d0440\n"
        ".word 0xeb0499cf\n"
        ".word 0xe1a03004\n"
        ".word 0xe1a02005\n"
        ".word 0xe3a01029\n"
        ".word 0xe3a00002\n"
        ".word 0xe88d0440\n"
        ".word 0xeb0499c9\n"
        ".word 0xe28ddf51\n"
        ".word 0xecbd8b06\n"
        ".word 0xe8bd8ff0\n"
        ".word 0xe3a0104a\n"
        ".word 0xe3a00029\n"
        ".word 0xeb049a21\n"
        ".word 0xe1a05000\n"
        ".word 0xe320f000\n"
        ".word 0xeaffffc2\n"
        ".word 0xe2840f76\n"
        ".word 0xe1d005f0\n"
        ".word 0xe3500003\n"
        ".word 0x13500001\n"
        ".word 0x03a08006\n"
        ".word 0x0affffe2\n"
        ".word 0xe3500002\n"
        ".word 0x13500000\n"
        ".word 0x03a05007\n"
        ".word 0xeaffffde\n"
    );
}
#if 0
// Original partial readable draft retained for reconstruction; not compiled.
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

    const Npc2dLayoutNode* node = LayoutNode(0x29, 0x11); // 0x00197F2C
    Quest_DrawIcon(quest_id, x0 + detail_offset + node->x,
                   y0 + node->y, 0x6A);                     // 0x00197F54

    node = LayoutNode(0x29, 0x12);                    // 0x00197F58
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
            LayoutNode(0x29, 5 + (i / 2));            // 0x00197FF8
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
    node = LayoutNode(0x29, 0x1A);                    // 0x00198058
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
            node = LayoutNode(0x29, 0x1B);
            Quest_DrawObjectiveIcon(row->primary_target,
                                    x0 + desc_offset + node->x,
                                    y0 + node->y, 0x6A);    // 0x00198238
            node = LayoutNode(0x29, 0x1C);
            UiFont_FormatString(text, "%s",
                                Quest_GetObjectiveName(row->primary_target));
            UiFont_DrawText(2, 0xFFFFFFFFu, text,
                            static_cast<f32>(x0 + desc_offset + node->x),
                            static_cast<f32>(y0 + node->y),
                            1.8f, 0.0f, 1.0f);              // 0x3EE66666
            const f32 width = Quest_MeasureText(text, 2);   // 0x001982B0
            const s32 extra = static_cast<s32>(width + 3.0f); // 0x40400000
            node = LayoutNode(0x29, 0x1B);
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
    node = LayoutNode(0x29, 0x1B);
    UiFont_DrawText(2, 0xFFFFFFFFu, text,
                    static_cast<f32>(x0 + desc_offset + node->x),
                    static_cast<f32>(y0 + node->y),
                    1.8f, 0.0f, 1.0f);                      // 0x3EE66666

    // 0x001981B0..0x00198438: main quest panel.  s21 (0.32) supplies the
    // shared lower-list offset; the 0.325 call belongs to the empty path.
    const s32 lower_offset = static_cast<s32>(
        UiGpu_TransformCoord(g_AsdGpuState, 0.32f));    // 0x3EA3D70A
    s32 panel_x = x0 + lower_offset;
    s32 panel_y = y0;
    if (screen_state == 0x17 || screen_state == 0x18 ||
        screen_state == 0x19) {                             // 0x001983E0
        panel_x = x0 + lower_offset +
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
    node = LayoutNode(0x29, 0x25);                    // 0x00198444
    UiAnimSprite_DrawAt(work->handle_5d8,
                        panel_x + node->x, panel_y + node->y,
                        0x6F, 6, 0, 1.0f);                  // 0x0019847C
    node = LayoutNode(0x29, 0x26);                    // 0x00198480
    UiAnimSprite_DrawAt(work->handle_5d8,
                        panel_x + node->x, panel_y + node->y,
                        0x6F, 6, 1, 1.0f);                  // 0x001984B4
    goto after_quest_preview;

draw_quest_preview:
    // 0x0019857C..0x00198678: 3D preview with two render-mode overrides.
    UiSprite_SetGlobalAlpha(*reinterpret_cast<const f32*>(
        reinterpret_cast<const u8*>(work) + 0x520 + 0x20)); // 0x00198580
    GpuModeSlotSet(0x2AC, static_cast<u32>(
        reinterpret_cast<std::uintptr_t>(UiGpu_SetRenderMode(6, 1, 0))));                    // 0x002c5fa4
    UiSprite_DrawNode(2, 0x29, 0x60, panel_x, panel_y, 0x68); // 0x001985F8
    GpuModeSlotSet(0x2AC, static_cast<u32>(
        reinterpret_cast<std::uintptr_t>(UiGpu_SetRenderMode(6, 7, 0)))); // 0x00198604
    UiSprite_SetGlobalAlpha(1.0f);                           // 0x0019864C
    UiSprite_DrawNode(2, 0x29, 0x24, panel_x, panel_y, 0x6A); // 0x0019866C

after_quest_preview:
    // 0x0019867C..0x00198784: quest availability / tracking flags.
    if ((*reinterpret_cast<const u8*>(reinterpret_cast<const u8*>(row) + 6) != 0 &&
         Quest_IsRewardKnown(quest_id))) {
        if (Quest_GetTrackedId() == quest_id) {             // 0x001986D0
            if (screen_state == 0x0C) {                     // 0x001986E4
                Quest_DrawRewardRow(reinterpret_cast<u8*>(work) + 0x264,
                                    static_cast<f32>(desc_offset)); // 0x00198728
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
        const s32 base_x = x0 + desc_offset;        // sl = 0.315 offset
        for (s32 i = 0; i < work->field_5d0; ++i) {
            if (work->field_5c8 == i) {                     // 0x0019879C
                continue;
            }
            node = LayoutNode(0x29, 0x48 + i);        // 0x001987A8
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
            } else {
                UiSprite_DrawNode(2, 0x29, 0x43, base_x + node->x,
                                  y0 + node->y, 0x6A);      // 0x001988CC
            }
        }
    }

    if (work->field_5c8 == 0) {                             // 0x00198810
        node = LayoutNode(0x29, 0x34);                // 0x001988E4
        const s32 list_x = x0 + lower_offset + node->x;
        const s32 list_y = lower_offset + node->y;
        for (s32 i = 0; i < 7; ++i) {
            UiAnimSprite_DrawAt(work->handle_5d4,
                                list_x, list_y + i * 0x11,
                                0x6F, 6, i, 1.0f);          // 0x00198914
        }
        const s32 bottom_offset = static_cast<s32>(
            UiGpu_TransformCoord(g_AsdGpuState, 0.315f));   // 0x00198928
        node = LayoutNode(0x29, 0x48);                // 0x00198944
        const s32 bx = x0 + bottom_offset + node->x;
        const s32 by = y0 + node->y;
        UiSprite_DrawNode(2, 0x29, 0x44, bx, by, 0x6F);     // 0x00198974
        UiSprite_DrawNode(2, 0x29, 0x45, bx, by, 0x74);     // 0x0019899C
    } else if (work->field_5c8 == 1 &&
               (*reinterpret_cast<const u8*>(
                    reinterpret_cast<const u8*>(row) + 7) & 0x40) != 0) {
        // 0x001989B8..0x00198C18: six reward detail rows.
        s32 drawn_rows = 0;
        bool extra_line = true;                             // [sp+0x138]
        for (s32 i = 0; i < 6; ++i) {
            QuestRewardEntry reward{};
            if (Quest_GetRewardEntry(quest_id, i, &reward)) { // 0x001989D8
                node = LayoutNode(0x29, 0x34);        // 0x001989F0
                char reward_text[0x80];
                char value_text[0x80];
                Quest_FormatReward(reward_text, static_cast<u16>(reward.field_08)); // 0x001989F8..0x00198A00
                const u32 reward_value = *reinterpret_cast<const u32*>(
                    reinterpret_cast<const u8*>(row) + 0x170 + i * 8);
                Quest_FormatReward(value_text, static_cast<u16>(reward_value)); // 0x00198A0C..0x00198A14
                UiFont_FormatString(
                    text, kQuestRewardFmt,
                    (*reinterpret_cast<const u8*>(
                         reinterpret_cast<const u8*>(&reward) + 6) != 0)
                        ? Quest_GetRewardItemName(reward.item_id)
                        : Item_GetShortNameString(reward.item_id),
                    reward_text, value_text);            // 0x00198A38..0x00198A48
                if (reward.field_08 < reward_value) {       // 0x00198A7C..0x00198AA0
                    extra_line = false;
                }
                UiFont_DrawText(3, 0x320202FFu, text,
                                static_cast<f32>(x0 + lower_offset + node->x),
                                static_cast<f32>(lower_offset + node->y + i * 0x11),
                                0.58f, 0.0f, 1.0f);     // 0x3F147AE1
                ++drawn_rows;
            }
        }
        // 0x00198AEC..0x00198B1C: completed, non-expired quests clear the
        // extra-line flag.
        if (*reinterpret_cast<const u8*>(reinterpret_cast<const u8*>(row) + 6) == 0 &&
            Quest_IsCompleted(quest_id) && !Quest_IsExpired(quest_id)) {
            extra_line = false;
        }
        // 0x00198B20..0x00198C14: one TBB row rendered below the reward
        // list.  The row index is 7 for value 1, 8 otherwise and 9 when the
        // quest is completed or +0x19C is zero (0x00198B58..0x00198CCC).
        if (*reinterpret_cast<const u8*>(reinterpret_cast<const u8*>(row) + 6) == 0 &&
            extra_line) {
            s32 row_index;
            node = LayoutNode(0x29, 0x34);      // 0x00198B38..0x00198B40
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
                    UiFont_FormatString(text, "%s",
                                        reinterpret_cast<const char*>(entry + 1));
                    UiFont_DrawText(3, 0x320202FFu, text,
                                    static_cast<f32>(x0 + lower_offset +
                                                     node->x),
                                    static_cast<f32>(lower_offset + node->y +
                                                     drawn_rows * 0x11 + 0x11),
                                    0.58f, 0.0f, 1.0f);       // 0x00198BCC
                }
            }
        }

        // 0x00198C18..0x00198C98: two hint panels.
        node = LayoutNode(0x29, 0x49);                // 0x00198C38
        UiSprite_DrawNode(2, 0x29, 0x44,
                          x0 + lower_offset + node->x,
                          y0 + node->y, 0x6F);              // 0x00198C6C
        UiSprite_DrawNode(2, 0x29, 0x46,
                          x0 + lower_offset + node->x,
                          y0 + node->y, 0x74);              // 0x00198C98
    } else if (work->field_5c8 == 2 ||
               (work->field_5c8 == 1 &&
                (*reinterpret_cast<const u8*>(
                     reinterpret_cast<const u8*>(row) + 7) & 0x40) == 0)) {
        // 0x00198CDC..0x00198D28: second seven-line list.
        node = LayoutNode(0x29, 0x34);                // 0x00198CEC
        const s32 list_x = x0 + lower_offset + node->x;
        const s32 list_y = lower_offset + node->y;
        for (s32 i = 0; i < 7; ++i) {
            UiAnimSprite_DrawAt(work->handle_5dc,
                                list_x, list_y + i * 0x11,
                                0x6F, 6, i, 1.0f);          // 0x00198D1C
        }
        if (work->field_5c8 == 2) {                         // 0x00198D40
            node = LayoutNode(0x29, 0x4A);            // 0x00198E44
        } else {
            node = LayoutNode(0x29, 0x49);
            UiSprite_DrawNode(2, 0x29, 0x44,
                              x0 + lower_offset + node->x,
                              y0 + node->y, 0x6F);          // 0x00198D8C
            UiSprite_DrawNode(2, 0x29, 0x47,
                              x0 + lower_offset + node->x,
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
#endif

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
__attribute__((naked)) void ui_func_001f0454(s32 x, s32 y, s32 mode, s32 flag, s32 has_target,
                      s32 slide_dir) {
    asm volatile(
        ".word 0xe92d5fff\n"
        ".word 0xed2d8b04\n"
        ".word 0xe24dde6a\n"
        ".word 0xeb01c977\n"
        ".word 0xe1b04000\n"
        ".word 0x0a00058d\n"
        ".word 0xe3a00000\n"
        ".word 0xe58d0690\n"
        ".word 0xe59d56b4\n"
        ".word 0xe59d66b0\n"
        ".word 0xe3a00065\n"
        ".word 0xe58d0004\n"
        ".word 0xed9f8aeb\n"
        ".word 0xe1a03006\n"
        ".word 0xe3a02001\n"
        ".word 0xe3a01024\n"
        ".word 0xe3a00002\n"
        ".word 0xe58d5000\n"
        ".word 0xeb033c2d\n"
        ".word 0xe3a0806a\n"
        ".word 0xe1a03006\n"
        ".word 0xe28820f9\n"
        ".word 0xe3a01024\n"
        ".word 0xe3a00002\n"
        ".word 0xe88d0120\n"
        ".word 0xeb033be8\n"
        ".word 0xe1a03006\n"
        ".word 0xe3a02f59\n"
        ".word 0xe3a01024\n"
        ".word 0xe3a00002\n"
        ".word 0xe88d0120\n"
        ".word 0xeb033be2\n"
        ".word 0xe3a0a06f\n"
        ".word 0xe1a03006\n"
        ".word 0xe28820fb\n"
        ".word 0xe3a01024\n"
        ".word 0xe3a00002\n"
        ".word 0xe88d0420\n"
        ".word 0xeb033bdb\n"
        ".word 0xe1a03006\n"
        ".word 0xe28820fc\n"
        ".word 0xe3a01024\n"
        ".word 0xe3a00002\n"
        ".word 0xe88d0120\n"
        ".word 0xeb033bd5\n"
        ".word 0xe1a03006\n"
        ".word 0xe28820fd\n"
        ".word 0xe3a01024\n"
        ".word 0xe3a00002\n"
        ".word 0xe88d0420\n"
        ".word 0xeb033bcf\n"
        ".word 0xe1a03006\n"
        ".word 0xe2882c01\n"
        ".word 0xe3a01024\n"
        ".word 0xe3a00002\n"
        ".word 0xe88d0120\n"
        ".word 0xeb033bc9\n"
        ".word 0xe1a03006\n"
        ".word 0xe28a20fc\n"
        ".word 0xe3a01024\n"
        ".word 0xe3a00002\n"
        ".word 0xe88d0420\n"
        ".word 0xeb033bc3\n"
        ".word 0xe3a09074\n"
        ".word 0xe1a03006\n"
        ".word 0xe3a02f5b\n"
        ".word 0xe3a01024\n"
        ".word 0xe3a00002\n"
        ".word 0xe88d0220\n"
        ".word 0xeb033bbc\n"
        ".word 0xe3a01f5a\n"
        ".word 0xe3a00024\n"
        ".word 0xeb033c55\n"
        ".word 0xe1a07000\n"
        ".word 0xe28dbd19\n"
        ".word 0xe28f2fad\n"
        ".word 0xe28f1fb2\n"
        ".word 0xe1a0000b\n"
        ".word 0xfa03389a\n"
        ".word 0xe1d710fa\n"
        ".word 0xe1d700f8\n"
        ".word 0xed9f9aae\n"
        ".word 0xe0811005\n"
        ".word 0xe0800006\n"
        ".word 0xee001a90\n"
        ".word 0xee000a10\n"
        ".word 0xeeb02a48\n"
        ".word 0xeef01a49\n"
        ".word 0xeeb01a49\n"
        ".word 0xe1a0200b\n"
        ".word 0xeef80ae0\n"
        ".word 0xeeb80ac0\n"
        ".word 0xe3a010ff\n"
        ".word 0xe3a00003\n"
        ".word 0xeb03386a\n"
        ".word 0xe28810ff\n"
        ".word 0xe3a00024\n"
        ".word 0xeb033c3c\n"
        ".word 0xe1a07000\n"
        ".word 0xe28f2f9d\n"
        ".word 0xe28f1f9a\n"
        ".word 0xe1a0000b\n"
        ".word 0xfa033882\n"
        ".word 0xe1d710fa\n"
        ".word 0xe1d700f8\n"
        ".word 0xeeb02a48\n"
        ".word 0xe0811005\n"
        ".word 0xe0800006\n"
        ".word 0xee001a90\n"
        ".word 0xee000a10\n"
        ".word 0xeef01a49\n"
        ".word 0xeeb01a49\n"
        ".word 0xe1a0200b\n"
        ".word 0xe3a010ff\n"
        ".word 0xeef80ae0\n"
        ".word 0xeeb80ac0\n"
        ".word 0xe3a00003\n"
        ".word 0xeb033853\n"
        ".word 0xe59403fc\n"
        ".word 0xe59f7240\n"
        ".word 0xe88d0420\n"
        ".word 0xe1a01fc0\n"
        ".word 0xe0800f21\n"
        ".word 0xe1a00140\n"
        ".word 0xe0c12097\n"
        ".word 0xe28920f9\n"
        ".word 0xe0411fc1\n"
        ".word 0xe0411101\n"
        ".word 0xe0800001\n"
        ".word 0xe0463000\n"
        ".word 0xe3a01024\n"
        ".word 0xe3a00002\n"
        ".word 0xeb033b7d\n"
        ".word 0xe2840024\n"
        ".word 0xed900a08\n"
        ".word 0xeb033c26\n"
        ".word 0xe59403fc\n"
        ".word 0xe88d0220\n"
        ".word 0xe1a01fc0\n"
        ".word 0xe0800f21\n"
        ".word 0xe1a00140\n"
        ".word 0xe0c12097\n"
        ".word 0xe2882f41\n"
        ".word 0xe0411fc1\n"
        ".word 0xe0411101\n"
        ".word 0xe0800001\n"
        ".word 0xe0463000\n"
        ".word 0xe3a01024\n"
        ".word 0xe3a00002\n"
        ".word 0xeb033b6c\n"
        ".word 0xeeb00a48\n"
        ".word 0xeb033c16\n"
        ".word 0xe1a03006\n"
        ".word 0xe3a0204f\n"
        ".word 0xe3a01024\n"
        ".word 0xe3a00002\n"
        ".word 0xe88d0120\n"
        ".word 0xeb033b64\n"
        ".word 0xe59d06bc\n"
        ".word 0xe3500000\n"
        ".word 0x0a000004\n"
        ".word 0xe59f019c\n"
        ".word 0xe19000b4\n"
        ".word 0xeb03231f\n"
        ".word 0xe58d002c\n"
        ".word 0xea000017\n"
        ".word 0xe59d06ec\n"
        ".word 0xe3500000\n"
        ".word 0x0a000009\n"
        ".word 0xe2841a01\n"
        ".word 0xe2811e39\n"
        ".word 0xe8910003\n"
        ".word 0xe1a01781\n"
        ".word 0xe18108a0\n"
        ".word 0xe1a008a0\n"
        ".word 0xeb032313\n"
        ".word 0xe58d002c\n"
        ".word 0xe320f000\n"
        ".word 0xea00000a\n"
        ".word 0xe59f0158\n"
        ".word 0xe19000b4\n"
        ".word 0xe0840180\n"
        ".word 0xe2801a01\n"
        ".word 0xe2811e39\n"
        ".word 0xe8910003\n"
        ".word 0xe1a01781\n"
        ".word 0xe18108a0\n"
        ".word 0xe1a008a0\n"
        ".word 0xeb032306\n"
        ".word 0xe58d002c\n"
        ".word 0xe3a0104d\n"
        ".word 0xe3a00024\n"
        ".word 0xeb033bdd\n"
        ".word 0xe1a07000\n"
        ".word 0xe59d002c\n"
        ".word 0xe1d000b0\n"
        ".word 0xeb0332bb\n"
        ".word 0xe1a02000\n"
        ".word 0xe28f10e0\n"
        ".word 0xe1a0000b\n"
        ".word 0xfa033820\n"
        ".word 0xe1d710fa\n"
        ".word 0xe1d700f8\n"
        ".word 0xeeb02a48\n"
        ".word 0xe0811005\n"
        ".word 0xe0800006\n"
        ".word 0xee001a90\n"
        ".word 0xee000a10\n"
        ".word 0xeef01a49\n"
        ".word 0xeeb01a49\n"
        ".word 0xe1a0200b\n"
        ".word 0xe3e01000\n"
        ".word 0xeef80ae0\n"
        ".word 0xeeb80ac0\n"
        ".word 0xe3a00002\n"
        ".word 0xeb0337f1\n"
        ".word 0xe3a0104e\n"
        ".word 0xe3a00024\n"
        ".word 0xeb033bc3\n"
        ".word 0xe1a07000\n"
        ".word 0xe59d002c\n"
        ".word 0xe3a01000\n"
        ".word 0xe1d000b0\n"
        ".word 0xeb033212\n"
        ".word 0xe1a02000\n"
        ".word 0xe28f1074\n"
        ".word 0xe1a0000b\n"
        ".word 0xfa033805\n"
        ".word 0xe1d710fa\n"
        ".word 0xe1d700f8\n"
        ".word 0xeeb02a48\n"
        ".word 0xe0811005\n"
        ".word 0xe0800006\n"
        ".word 0xee001a90\n"
        ".word 0xee000a10\n"
        ".word 0xeef01a49\n"
        ".word 0xeeb01a49\n"
        ".word 0xe59f1074\n"
        ".word 0xe1a0200b\n"
        ".word 0xeef80ae0\n"
        ".word 0xeeb80ac0\n"
        ".word 0xe3a00002\n"
        ".word 0xeb0337d6\n"
        ".word 0xe3a01051\n"
        ".word 0xe3a00024\n"
        ".word 0xeb033ba8\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xea000013\n"
        ".word 0x3f800000\n"
        ".word 0x8e826882\n"
        ".word 0x85828882\n"
        ".word 0x89829282\n"
        ".word 0x89829482\n"
        ".word 0x87828e82\n"
        ".word 0x00000000\n"
        ".word 0x00007325\n"
        ".word 0x00000000\n"
        ".word 0x81826f82\n"
        ".word 0x85829282\n"
        ".word 0x94828e82\n"
        ".word 0x72824081\n"
        ".word 0x89828b82\n"
        ".word 0x8c828c82\n"
        ".word 0x00009382\n"
        ".word 0x55555556\n"
        ".word 0x00005210\n"
        ".word 0x00006ce2\n"
        ".word 0xf49800ff\n"
        ".word 0xe59dc02c\n"
        ".word 0xe28f3fb7\n"
        ".word 0xe3a01002\n"
        ".word 0xe3a0208d\n"
        ".word 0xe5dcc003\n"
        ".word 0xe88d100e\n"
        ".word 0xe3a03001\n"
        ".word 0xe1d010fa\n"
        ".word 0xe1d000f8\n"
        ".word 0xe0812005\n"
        ".word 0xe0801006\n"
        ".word 0xe3a00000\n"
        ".word 0xeb03362b\n"
        ".word 0xe2840a09\n"
        ".word 0xe2800e1a\n"
        ".word 0xe3a09000\n"
        ".word 0xe1a07000\n"
        ".word 0xeb02b404\n"
        ".word 0xe3500000\n"
        ".word 0xe320f000\n"
        ".word 0xda00000a\n"
        ".word 0xe0840089\n"
        ".word 0xe2800a09\n"
        ".word 0xe1d001b0\n"
        ".word 0xe3500000\n"
        ".word 0x0a000005\n"
        ".word 0xe2899001\n"
        ".word 0xe1a00007\n"
        ".word 0xeb02b3f9\n"
        ".word 0xe1500009\n"
        ".word 0xe320f000\n"
        ".word 0xcafffff4\n"
        ".word 0xe59f1264\n"
        ".word 0xe3a00024\n"
        ".word 0xeb033b6e\n"
        ".word 0xe1a07000\n"
        ".word 0xe3a00000\n"
        ".word 0xe58d0000\n"
        ".word 0xe1d710fa\n"
        ".word 0xe1d720f8\n"
        ".word 0xe59d002c\n"
        ".word 0xe0811005\n"
        ".word 0xe082c006\n"
        ".word 0xe1a02001\n"
        ".word 0xe1d000f0\n"
        ".word 0xe3a0308d\n"
        ".word 0xe1a0100c\n"
        ".word 0xeb031853\n"
        ".word 0xe1d710fa\n"
        ".word 0xe1d720f8\n"
        ".word 0xe59d002c\n"
        ".word 0xe081c005\n"
        ".word 0xe0821006\n"
        ".word 0xe3a03092\n"
        ".word 0xe1d000b0\n"
        ".word 0xe1a0200c\n"
        ".word 0xeb019e66\n"
        ".word 0xe59d002c\n"
        ".word 0xe28d5030\n"
        ".word 0xe1a01005\n"
        ".word 0xe1d000b0\n"
        ".word 0xeb02b564\n"
        ".word 0xe1a00005\n"
        ".word 0xe320f000\n"
        ".word 0xeb02b081\n"
        ".word 0xe58d0018\n"
        ".word 0xe2840a09\n"
        ".word 0xe58d0694\n"
        ".word 0xe2840a09\n"
        ".word 0xeddf9a75\n"
        ".word 0xe2800f81\n"
        ".word 0xe3a06000\n"
        ".word 0xe58d063c\n"
        ".word 0xeef08a48\n"
        ".word 0xe2861c01\n"
        ".word 0xe59d76b4\n"
        ".word 0xe59d86b0\n"
        ".word 0xe281107d\n"
        ".word 0xe3a00024\n"
        ".word 0xeb033b41\n"
        ".word 0xe1a05000\n"
        ".word 0xe59d0018\n"
        ".word 0xe1560000\n"
        ".word 0xba00001e\n"
        ".word 0xe1d500fa\n"
        ".word 0xe3a0a065\n"
        ".word 0xe28a2f71\n"
        ".word 0xe0800007\n"
        ".word 0xe88d0401\n"
        ".word 0xe1d500f8\n"
        ".word 0xe3a01024\n"
        ".word 0xe0803008\n"
        ".word 0xe3a00002\n"
        ".word 0xeb033a97\n"
        ".word 0xe1d500fa\n"
        ".word 0xe59f2170\n"
        ".word 0xe3a01024\n"
        ".word 0xe0800007\n"
        ".word 0xe88d0401\n"
        ".word 0xe1d500f8\n"
        ".word 0xe0803008\n"
        ".word 0xe3a00002\n"
        ".word 0xeb033a8e\n"
        ".word 0xe1d500fa\n"
        ".word 0xe3a02e17\n"
        ".word 0xe3a01024\n"
        ".word 0xe0800007\n"
        ".word 0xe88d0401\n"
        ".word 0xe1d500f8\n"
        ".word 0xe0803008\n"
        ".word 0xe3a00002\n"
        ".word 0xeb033a85\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xea0001a0\n"
        ".word 0xe59d0694\n"
        ".word 0xe590026c\n"
        ".word 0xe0490000\n"
        ".word 0xe1560000\n"
        ".word 0xaa00000d\n"
        ".word 0xe1d500fa\n"
        ".word 0xe59f210c\n"
        ".word 0xe0801007\n"
        ".word 0xe3a00065\n"
        ".word 0xe58d0004\n"
        ".word 0xe58d1000\n"
        ".word 0xe1d500f8\n"
        ".word 0xe3a01024\n"
        ".word 0xe0803008\n"
        ".word 0xe3a00002\n"
        ".word 0xeb033a72\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xea0000a3\n"
        ".word 0xe59d063c\n"
        ".word 0xeb02b992\n"
        ".word 0xe59d1694\n"
        ".word 0xe591126c\n"
        ".word 0xe1500001\n"
        ".word 0xda000025\n"
        ".word 0xe1560009\n"
        ".word 0x1a000023\n"
        ".word 0xe59d06b8\n"
        ".word 0xe3500001\n"
        ".word 0x0a000003\n"
        ".word 0xe3500002\n"
        ".word 0x13500003\n"
        ".word 0x1a000008\n"
        ".word 0xea000015\n"
        ".word 0xe59403fc\n"
        ".word 0xe3500001\n"
        ".word 0xaa000004\n"
        ".word 0xe2600001\n"
        ".word 0xee000a10\n"
        ".word 0xeef88ac0\n"
        ".word 0xeeb00a68\n"
        ".word 0xeb033b04\n"
        ".word 0xe1d500fa\n"
        ".word 0xe59f207c\n"
        ".word 0xe0801007\n"
        ".word 0xe3a00065\n"
        ".word 0xe58d0004\n"
        ".word 0xe58d1000\n"
        ".word 0xe1d500f8\n"
        ".word 0xe3a01024\n"
        ".word 0xe0803008\n"
        ".word 0xe3a00002\n"
        ".word 0xeb033a4d\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xea00007e\n"
        ".word 0xe59d0690\n"
        ".word 0xe3500000\n"
        ".word 0x0affffee\n"
        ".word 0xe59403fc\n"
        ".word 0xe0400100\n"
        ".word 0xe0877000\n"
        ".word 0xeaffffea\n"
        ".word 0xe59d06b8\n"
        ".word 0xe3500001\n"
        ".word 0x0a00000a\n"
        ".word 0xe3500002\n"
        ".word 0x0a000027\n"
        ".word 0xe3500003\n"
        ".word 0x0a000046\n"
        ".word 0xea000064\n"
        ".word 0x00006425\n"
        ".word 0x000001ed\n"
        ".word 0x3e4ccccd\n"
        ".word 0x0000016f\n"
        ".word 0x00000172\n"
        ".word 0x00000173\n"
        ".word 0xe59403fc\n"
        ".word 0xe3500001\n"
        ".word 0xba00005b\n"
        ".word 0xe59d063c\n"
        ".word 0xeb02b9b0\n"
        ".word 0xe1a0a000\n"
        ".word 0xe59d063c\n"
        ".word 0xeb02b9a7\n"
        ".word 0xe080000a\n"
        ".word 0xe0841086\n"
        ".word 0xe0840080\n"
        ".word 0xe2811a09\n"
        ".word 0xe2800a09\n"
        ".word 0xe1d111b0\n"
        ".word 0xe1d002b0\n"
        ".word 0xe1510000\n"
        ".word 0x1a00004d\n"
        ".word 0xe2840e2e\n"
        ".word 0xeb0338e9\n"
        ".word 0xe0888000\n"
        ".word 0xe2840e2e\n"
        ".word 0xeb0338e3\n"
        ".word 0xe0877000\n"
        ".word 0xe2840e2e\n"
        ".word 0xed900a08\n"
        ".word 0xeef08a40\n"
        ".word 0xe320f000\n"
        ".word 0xeb033ac5\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xea00003f\n"
        ".word 0xe59403fc\n"
        ".word 0xe3500005\n"
        ".word 0xca00003c\n"
        ".word 0xe59d063c\n"
        ".word 0xeb02b991\n"
        ".word 0xe1a0a000\n"
        ".word 0xe59d063c\n"
        ".word 0xeb02b988\n"
        ".word 0xe59d1690\n"
        ".word 0xe080000a\n"
        ".word 0xe3510000\n"
        ".word 0x0a000002\n"
        ".word 0xe59413fc\n"
        ".word 0xe0411101\n"
        ".word 0xe0877001\n"
        ".word 0xe0841086\n"
        ".word 0xe0840080\n"
        ".word 0xe2811a09\n"
        ".word 0xe2800a09\n"
        ".word 0xe1d111b0\n"
        ".word 0xe1d002b0\n"
        ".word 0xe1510000\n"
        ".word 0x1a000028\n"
        ".word 0xe59403fc\n"
        ".word 0xe2600005\n"
        ".word 0xee000a10\n"
        ".word 0xeeb80ac0\n"
        ".word 0xee608a29\n"
        ".word 0xeeb00a68\n"
        ".word 0xeb033aa4\n"
        ".word 0xe3a00001\n"
        ".word 0xe58d0690\n"
        ".word 0xea00001e\n"
        ".word 0xe59433fc\n"
        ".word 0xe3530005\n"
        ".word 0xca00001b\n"
        ".word 0xe59d0690\n"
        ".word 0xe3500000\n"
        ".word 0x10430103\n"
        ".word 0x10877000\n"
        ".word 0xe3a00007\n"
        ".word 0xe0841080\n"
        ".word 0xe2811a09\n"
        ".word 0xe1d121b0\n"
        ".word 0xe3520000\n"
        ".word 0x1a000007\n"
        ".word 0xe1d110be\n"
        ".word 0xe3510000\n"
        ".word 0x0a000001\n"
        ".word 0xe2400001\n"
        ".word 0xea000002\n"
        ".word 0xe2400002\n"
        ".word 0xe3700001\n"
        ".word 0xcafffff2\n"
        ".word 0xe1560000\n"
        ".word 0x1a000007\n"
        ".word 0xe2630005\n"
        ".word 0xee000a10\n"
        ".word 0xeeb80ac0\n"
        ".word 0xee608a29\n"
        ".word 0xeeb00a68\n"
        ".word 0xeb033a84\n"
        ".word 0xe3a00001\n"
        ".word 0xe58d0690\n"
        ".word 0xe1d500fa\n"
        ".word 0xe59f24f0\n"
        ".word 0xe0801007\n"
        ".word 0xe3a00065\n"
        ".word 0xe58d0004\n"
        ".word 0xe58d1000\n"
        ".word 0xe1d500f8\n"
        ".word 0xe3a01024\n"
        ".word 0xe0803008\n"
        ".word 0xe3a00002\n"
        ".word 0xeb0339cb\n"
        ".word 0xe1d500fa\n"
        ".word 0xe3a0a065\n"
        ".word 0xe51f21c4\n"
        ".word 0xe0800007\n"
        ".word 0xe88d0401\n"
        ".word 0xe1d500f8\n"
        ".word 0xe3a01024\n"
        ".word 0xe0803008\n"
        ".word 0xe3a00002\n"
        ".word 0xeb0339c1\n"
        ".word 0xe1d500fa\n"
        ".word 0xe3a02e17\n"
        ".word 0xe3a01024\n"
        ".word 0xe0800007\n"
        ".word 0xe88d0401\n"
        ".word 0xe1d500f8\n"
        ".word 0xe0803008\n"
        ".word 0xe3a00002\n"
        ".word 0xeb0339b8\n"
        ".word 0xe0840086\n"
        ".word 0xe280aa09\n"
        ".word 0xe1da01b0\n"
        ".word 0xe3500000\n"
        ".word 0x0a00006c\n"
        ".word 0xe1d500fa\n"
        ".word 0xe3a0b06a\n"
        ".word 0xe3a02f5d\n"
        ".word 0xe0800007\n"
        ".word 0xe88d0801\n"
        ".word 0xe1d500f8\n"
        ".word 0xe3a01024\n"
        ".word 0xe0803008\n"
        ".word 0xe3a00002\n"
        ".word 0xeb0339a9\n"
        ".word 0xe1d500fa\n"
        ".word 0xe59f2440\n"
        ".word 0xe3a01024\n"
        ".word 0xe0800007\n"
        ".word 0xe88d0801\n"
        ".word 0xe1d500f8\n"
        ".word 0xe0803008\n"
        ".word 0xe3a00002\n"
        ".word 0xeb0339a0\n"
        ".word 0xe1d500fa\n"
        ".word 0xe28b2f43\n"
        ".word 0xe0801007\n"
        ".word 0xe3a0006f\n"
        ".word 0xe58d0004\n"
        ".word 0xe58d1000\n"
        ".word 0xe1d500f8\n"
        ".word 0xe3a01024\n"
        ".word 0xe0803008\n"
        ".word 0xe3a00002\n"
        ".word 0xeb033995\n"
        ".word 0xe59d0694\n"
        ".word 0xe3a0b0ff\n"
        ".word 0xe590026c\n"
        ".word 0xe0490000\n"
        ".word 0xe1500006\n"
        ".word 0xe1da01b0\n"
        ".word 0xc3e0b000\n"
        ".word 0xeb033071\n"
        ".word 0xe1a02000\n"
        ".word 0xe28f1ff5\n"
        ".word 0xe28d0d19\n"
        ".word 0xfa033670\n"
        ".word 0xe3a01f5e\n"
        ".word 0xe3a00024\n"
        ".word 0xeb033a22\n"
        ".word 0xe1d020fa\n"
        ".word 0xe1d510fa\n"
        ".word 0xe1d530f8\n"
        ".word 0xe1d000f8\n"
        ".word 0xe0811002\n"
        ".word 0xe0811007\n"
        ".word 0xe0800003\n"
        ".word 0xe0800008\n"
        ".word 0xee001a10\n"
        ".word 0xee010a10\n"
        ".word 0xeeb02a68\n"
        ".word 0xe28d2d19\n"
        ".word 0xe1a0100b\n"
        ".word 0xe3a00002\n"
        ".word 0xeef80ac0\n"
        ".word 0xeeb80ac1\n"
        ".word 0xeeb01a49\n"
        ".word 0xeef01a41\n"
        ".word 0xeb03363a\n"
        ".word 0xe59f1374\n"
        ".word 0xe3a00024\n"
        ".word 0xeb033a0c\n"
        ".word 0xe3a01000\n"
        ".word 0xe58d1000\n"
        ".word 0xe58d1004\n"
        ".word 0xe1d510fa\n"
        ".word 0xe1d020fa\n"
        ".word 0xe1d530f8\n"
        ".word 0xe1d0c0f8\n"
        ".word 0xe0811002\n"
        ".word 0xe0812007\n"
        ".word 0xe083300c\n"
        ".word 0xe0831008\n"
        ".word 0xe1da01f0\n"
        ".word 0xe3a03074\n"
        ".word 0xeb031827\n"
        ".word 0xe3a01f5f\n"
        ".word 0xe3a00024\n"
        ".word 0xeb0339fb\n"
        ".word 0xe1a0b000\n"
        ".word 0xe1da01b0\n"
        ".word 0xeb02a734\n"
        ".word 0xe3a01004\n"
        ".word 0xe58d1000\n"
        ".word 0xe1a03000\n"
        ".word 0xe28d1004\n"
        ".word 0xe24f2fe5\n"
        ".word 0xe3a00079\n"
        ".word 0xe881000d\n"
        ".word 0xe1d510fa\n"
        ".word 0xe1d530f8\n"
        ".word 0xe1db20fa\n"
        ".word 0xe1db00f8\n"
        ".word 0xe0811002\n"
        ".word 0xe0800003\n"
        ".word 0xe0812007\n"
        ".word 0xe0801008\n"
        ".word 0xe3a03001\n"
        ".word 0xe1a00003\n"
        ".word 0xeb03348d\n"
        ".word 0xe59d06b8\n"
        ".word 0xe3500001\n"
        ".word 0x1a000063\n"
        ".word 0xea00001c\n"
        ".word 0xe28dbd19\n"
        ".word 0xe28f1d0b\n"
        ".word 0xe1a0000b\n"
        ".word 0xfa033629\n"
        ".word 0xe3a01f5e\n"
        ".word 0xe3a00024\n"
        ".word 0xeb0339db\n"
        ".word 0xe1d020fa\n"
        ".word 0xe1d510fa\n"
        ".word 0xe1d530f8\n"
        ".word 0xe1d000f8\n"
        ".word 0xe0811002\n"
        ".word 0xe0811007\n"
        ".word 0xe0800003\n"
        ".word 0xe0800008\n"
        ".word 0xee001a90\n"
        ".word 0xee000a10\n"
        ".word 0xeeb01a49\n"
        ".word 0xeeb02a68\n"
        ".word 0xe1a0200b\n"
        ".word 0xe3a010ff\n"
        ".word 0xeef80ae0\n"
        ".word 0xeeb80ac0\n"
        ".word 0xeef01a41\n"
        ".word 0xe3a00002\n"
        ".word 0xeb0335f3\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xeaffffde\n"
        ".word 0xe59403fc\n"
        ".word 0xe3500005\n"
        ".word 0xba000042\n"
        ".word 0xe59d063c\n"
        ".word 0xeb02b8a4\n"
        ".word 0xe1a0b000\n"
        ".word 0xe59d063c\n"
        ".word 0xeb02b89b\n"
        ".word 0xe080000b\n"
        ".word 0xe1da11b0\n"
        ".word 0xe0840080\n"
        ".word 0xe2800a09\n"
        ".word 0xe1d002b0\n"
        ".word 0xe1510000\n"
        ".word 0x1a000036\n"
        ".word 0xe2840fdb\n"
        ".word 0xed900a08\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xeb0339c1\n"
        ".word 0xe59fb20c\n"
        ".word 0xe3a02000\n"
        ".word 0xe3a01001\n"
        ".word 0xe3a00006\n"
        ".word 0xe59ba000\n"
        ".word 0xeb0353e0\n"
        ".word 0xe28aaa01\n"
        ".word 0xe28aafab\n"
        ".word 0xe59a1000\n"
        ".word 0xe08a2101\n"
        ".word 0xe5921008\n"
        ".word 0xe5820008\n"
        ".word 0xe5da2018\n"
        ".word 0xe3520000\n"
        ".word 0x01510000\n"
        ".word 0x0a000003\n"
        ".word 0xe59a101c\n"
        ".word 0xe12fff31\n"
        ".word 0xe3a00000\n"
        ".word 0xe5ca0018\n"
        ".word 0xe1d510fa\n"
        ".word 0xe3a00065\n"
        ".word 0xe58d0004\n"
        ".word 0xe0811007\n"
        ".word 0xe58d1000\n"
        ".word 0xe1d500f8\n"
        ".word 0xe51f24f4\n"
        ".word 0xe3a01024\n"
        ".word 0xe0803008\n"
        ".word 0xe3a00002\n"
        ".word 0xeb0338f6\n"
        ".word 0xe59b5000\n"
        ".word 0xe3a02000\n"
        ".word 0xe3a01007\n"
        ".word 0xe3a00006\n"
        ".word 0xeb0353c2\n"
        ".word 0xe2855a01\n"
        ".word 0xe2855fab\n"
        ".word 0xe5951000\n"
        ".word 0xe0851101\n"
        ".word 0xe5912008\n"
        ".word 0xe5810008\n"
        ".word 0xe5d51018\n"
        ".word 0xe3510000\n"
        ".word 0x01520000\n"
        ".word 0x0a000003\n"
        ".word 0xe595101c\n"
        ".word 0xe12fff31\n"
        ".word 0xe3a00000\n"
        ".word 0xe5c50018\n"
        ".word 0xeeb00a48\n"
        ".word 0xeb03398d\n"
        ".word 0xe2866001\n"
        ".word 0xe3560008\n"
        ".word 0xbafffe31\n"
        ".word 0xe28d0e6b\n"
        ".word 0xe3a0b000\n"
        ".word 0xe8900060\n"
        ".word 0xe2842a09\n"
        ".word 0xe58db680\n"
        ".word 0xe59d002c\n"
        ".word 0xe58db684\n"
        ".word 0xe58db688\n"
        ".word 0xe58db68c\n"
        ".word 0xe58db000\n"
        ".word 0xe5d01003\n"
        ".word 0xe1d000b0\n"
        ".word 0xe28d7d1a\n"
        ".word 0xe2822010\n"
        ".word 0xe1a03007\n"
        ".word 0xe58d2028\n"
        ".word 0xeb01e6c2\n"
        ".word 0xe3a09000\n"
        ".word 0xe0870089\n"
        ".word 0xe1d010b0\n"
        ".word 0xe3510000\n"
        ".word 0x0a000005\n"
        ".word 0xe1d000b2\n"
        ".word 0xe3500000\n"
        ".word 0x0a000051\n"
        ".word 0xe2899002\n"
        ".word 0xe3590008\n"
        ".word 0xbafffff5\n"
        ".word 0xe3590000\n"
        ".word 0xc3a08000\n"
        ".word 0xc3a0a065\n"
        ".word 0xca00004c\n"
        ".word 0xe59f10b4\n"
        ".word 0xe3a00024\n"
        ".word 0xeb033957\n"
        ".word 0xe1a07000\n"
        ".word 0xe1d000fa\n"
        ".word 0xe3a08065\n"
        ".word 0xe51f2608\n"
        ".word 0xe0800006\n"
        ".word 0xe88d0101\n"
        ".word 0xe1d700f8\n"
        ".word 0xe3a01024\n"
        ".word 0xe0803005\n"
        ".word 0xe3a00002\n"
        ".word 0xeb0338b0\n"
        ".word 0xe1d700fa\n"
        ".word 0xe3a02e17\n"
        ".word 0xe3a01024\n"
        ".word 0xe0800006\n"
        ".word 0xe88d0101\n"
        ".word 0xe1d700f8\n"
        ".word 0xe0803005\n"
        ".word 0xe3a00002\n"
        ".word 0xeb0338a7\n"
        ".word 0xe1d700fa\n"
        ".word 0xe2882f43\n"
        ".word 0xe3a01024\n"
        ".word 0xe0800006\n"
        ".word 0xe88d0101\n"
        ".word 0xe1d700f8\n"
        ".word 0xe0803005\n"
        ".word 0xe3a00002\n"
        ".word 0xeb03389e\n"
        ".word 0xe3a01f5e\n"
        ".word 0xe3a00024\n"
        ".word 0xeb033937\n"
        ".word 0xe1a08000\n"
        ".word 0xe28f1028\n"
        ".word 0xe28d9d19\n"
        ".word 0xea00000b\n"
        ".word 0x00000171\n"
        ".word 0x00000175\n"
        ".word 0x00007325\n"
        ".word 0x00000177\n"
        ".word 0x81207c81\n"
        ".word 0x7c81207c\n"
        ".word 0x00000000\n"
        ".word 0x0044ea00\n"
        ".word 0x00000197\n"
        ".word 0x8f826d82\n"
        ".word 0x85828e82\n"
        ".word 0x00000000\n"
        ".word 0xe1a00009\n"
        ".word 0xfa033570\n"
        ".word 0xe1d700fa\n"
        ".word 0xe1d810fa\n"
        ".word 0xe1d720f8\n"
        ".word 0xe1d830f8\n"
        ".word 0xe0800001\n"
        ".word 0xe0800006\n"
        ".word 0xe0821003\n"
        ".word 0xe0811005\n"
        ".word 0xee000a90\n"
        ".word 0xee001a10\n"
        ".word 0xeeb01a49\n"
        ".word 0xeeb02a48\n"
        ".word 0xe59f16fc\n"
        ".word 0xe1a02009\n"
        ".word 0xeef80ae0\n"
        ".word 0xeeb80ac0\n"
        ".word 0xeef01a41\n"
        ".word 0xe3a00002\n"
        ".word 0xeb03353d\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xea000040\n"
        ".word 0xe2899001\n"
        ".word 0xeaffffae\n"
        ".word 0xe2881c01\n"
        ".word 0xe2811093\n"
        ".word 0xe3a00024\n"
        ".word 0xeb033909\n"
        ".word 0xe1a07000\n"
        ".word 0xe1d000fa\n"
        ".word 0xe59f26b8\n"
        ".word 0xe3a01024\n"
        ".word 0xe0800006\n"
        ".word 0xe88d0401\n"
        ".word 0xe1d700f8\n"
        ".word 0xe0803005\n"
        ".word 0xe3a00002\n"
        ".word 0xeb033863\n"
        ".word 0xe1d700fa\n"
        ".word 0xe59f2698\n"
        ".word 0xe3a01024\n"
        ".word 0xe0800006\n"
        ".word 0xe88d0401\n"
        ".word 0xe1d700f8\n"
        ".word 0xe0803005\n"
        ".word 0xe3a00002\n"
        ".word 0xeb03385a\n"
        ".word 0xe1d700fa\n"
        ".word 0xe3a02e19\n"
        ".word 0xe3a01024\n"
        ".word 0xe0800006\n"
        ".word 0xe88d0401\n"
        ".word 0xe1d700f8\n"
        ".word 0xe0803005\n"
        ".word 0xe3a00002\n"
        ".word 0xeb033851\n"
        ".word 0xe1d700fa\n"
        ".word 0xe3a0106a\n"
        ".word 0xe59f2650\n"
        ".word 0xe0800006\n"
        ".word 0xe1cd00f0\n"
        ".word 0xe1d700f8\n"
        ".word 0xe3a01024\n"
        ".word 0xe0803005\n"
        ".word 0xe3a00002\n"
        ".word 0xeb033847\n"
        ".word 0xe59f1634\n"
        ".word 0xe3a00024\n"
        ".word 0xeb0338e0\n"
        ".word 0xe58db000\n"
        ".word 0xe58db004\n"
        ".word 0xe1d020fa\n"
        ".word 0xe1d710fa\n"
        ".word 0xe1d730f8\n"
        ".word 0xe1d000f8\n"
        ".word 0xe0811002\n"
        ".word 0xe0812006\n"
        ".word 0xe0800003\n"
        ".word 0xe0801005\n"
        ".word 0xe28d0d1a\n"
        ".word 0xe0800088\n"
        ".word 0xe3a0306f\n"
        ".word 0xe1d000f0\n"
        ".word 0xeb0316fa\n"
        ".word 0xe2888001\n"
        ".word 0xe1590008\n"
        ".word 0xcaffffc0\n"
        ".word 0xe59d063c\n"
        ".word 0xeb02b7b0\n"
        ".word 0xe3a08000\n"
        ".word 0xe58d0014\n"
        ".word 0xe59d06e8\n"
        ".word 0xe3500000\n"
        ".word 0x0a000004\n"
        ".word 0xe59d063c\n"
        ".word 0xeb02b7a3\n"
        ".word 0xe1500008\n"
        ".word 0xe320f000\n"
        ".word 0x0a000093\n"
        ".word 0xe2881c01\n"
        ".word 0xe2811085\n"
        ".word 0xe3a00024\n"
        ".word 0xeb0338be\n"
        ".word 0xe1a07000\n"
        ".word 0xe1d000fa\n"
        ".word 0xe3a09065\n"
        ".word 0xe51f286c\n"
        ".word 0xe0800006\n"
        ".word 0xe88d0201\n"
        ".word 0xe1d700f8\n"
        ".word 0xe3a01024\n"
        ".word 0xe0803005\n"
        ".word 0xe3a00002\n"
        ".word 0xeb033817\n"
        ".word 0xe1d700fa\n"
        ".word 0xe3a02e17\n"
        ".word 0xe3a01024\n"
        ".word 0xe0800006\n"
        ".word 0xe88d0201\n"
        ".word 0xe1d700f8\n"
        ".word 0xe0803005\n"
        ".word 0xe3a00002\n"
        ".word 0xeb03380e\n"
        ".word 0xe1d700fa\n"
        ".word 0xe2892f43\n"
        ".word 0xe3a01024\n"
        ".word 0xe0800006\n"
        ".word 0xe88d0201\n"
        ".word 0xe1d700f8\n"
        ".word 0xe0803005\n"
        ".word 0xe3a00002\n"
        ".word 0xeb033805\n"
        ".word 0xe59d063c\n"
        ".word 0xe320f000\n"
        ".word 0xeb02b123\n"
        ".word 0xe1500008\n"
        ".word 0xe320f000\n"
        ".word 0xda00006c\n"
        ".word 0xe1d700fa\n"
        ".word 0xe3a0906a\n"
        ".word 0xe3a02f5d\n"
        ".word 0xe0800006\n"
        ".word 0xe88d0201\n"
        ".word 0xe1d700f8\n"
        ".word 0xe3a01024\n"
        ".word 0xe0803005\n"
        ".word 0xe3a00002\n"
        ".word 0xeb0337f5\n"
        ".word 0xe1d700fa\n"
        ".word 0xe51f2290\n"
        ".word 0xe3a01024\n"
        ".word 0xe0800006\n"
        ".word 0xe88d0201\n"
        ".word 0xe1d700f8\n"
        ".word 0xe0803005\n"
        ".word 0xe3a00002\n"
        ".word 0xeb0337ec\n"
        ".word 0xe1d700fa\n"
        ".word 0xe2892f43\n"
        ".word 0xe0801006\n"
        ".word 0xe3a0006f\n"
        ".word 0xe58d0004\n"
        ".word 0xe58d1000\n"
        ".word 0xe1d700f8\n"
        ".word 0xe3a01024\n"
        ".word 0xe0803005\n"
        ".word 0xe3a00002\n"
        ".word 0xeb0337e1\n"
        ".word 0xe59d0014\n"
        ".word 0xe3a0a0ff\n"
        ".word 0xe3a01008\n"
        ".word 0xe0800008\n"
        ".word 0xe0840080\n"
        ".word 0xe2809a09\n"
        ".word 0xe59d0028\n"
        ".word 0xe1d922b0\n"
        ".word 0xeb02aee0\n"
        ".word 0xe3500000\n"
        ".word 0xe1d902b0\n"
        ".word 0x128aa721\n"
        ".word 0xeb032eb8\n"
        ".word 0xe1a02000\n"
        ".word 0xe24f1e31\n"
        ".word 0xe28d0d19\n"
        ".word 0xfa0334b7\n"
        ".word 0xe3a01f5e\n"
        ".word 0xe3a00024\n"
        ".word 0xeb033869\n"
        ".word 0xe1d020fa\n"
        ".word 0xe1d710fa\n"
        ".word 0xe1d730f8\n"
        ".word 0xe1d000f8\n"
        ".word 0xe0811002\n"
        ".word 0xe0811006\n"
        ".word 0xe0800003\n"
        ".word 0xe0800005\n"
        ".word 0xee001a10\n"
        ".word 0xee010a10\n"
        ".word 0xeeb02a48\n"
        ".word 0xe28d2d19\n"
        ".word 0xe1a0100a\n"
        ".word 0xe3a00002\n"
        ".word 0xeef80ac0\n"
        ".word 0xeeb80ac1\n"
        ".word 0xeeb01a49\n"
        ".word 0xeef01a41\n"
        ".word 0xeb033481\n"
        ".word 0xe51f1370\n"
        ".word 0xe3a00024\n"
        ".word 0xeb033853\n"
        ".word 0xe58db000\n"
        ".word 0xe58db004\n"
        ".word 0xe1d710fa\n"
        ".word 0xe1d020fa\n"
        ".word 0xe1d730f8\n"
        ".word 0xe1d0c0f8\n"
        ".word 0xe0811002\n"
        ".word 0xe0812006\n"
        ".word 0xe083300c\n"
        ".word 0xe0831005\n"
        ".word 0xe1d902f0\n"
        ".word 0xe3a03074\n"
        ".word 0xeb03166f\n"
        ".word 0xe3a01f5f\n"
        ".word 0xe3a00024\n"
        ".word 0xeb033843\n"
        ".word 0xe1a0a000\n"
        ".word 0xe1d902b0\n"
        ".word 0xeb02a57c\n"
        ".word 0xe1a03000\n"
        ".word 0xe3a01004\n"
        ".word 0xe28dc004\n"
        ".word 0xe28f2e3a\n"
        ".word 0xe3a00079\n"
        ".word 0xe58d1000\n"
        ".word 0xe88c000d\n"
        ".word 0xe1d710f8\n"
        ".word 0xe1da30f8\n"
        ".word 0xe1d700fa\n"
        ".word 0xe1da20fa\n"
        ".word 0xe0811003\n"
        ".word 0xe3a03001\n"
        ".word 0xe0800002\n"
        ".word 0xe0802006\n"
        ".word 0xe0811005\n"
        ".word 0xe1a00003\n"
        ".word 0xeb0332d5\n"
        ".word 0xe2888001\n"
        ".word 0xe3580008\n"
        ".word 0xbaffff60\n"
        ".word 0xe59d063c\n"
        ".word 0xeb02b70d\n"
        ".word 0xe1a07000\n"
        ".word 0xe59d063c\n"
        ".word 0xeb02b704\n"
        ".word 0xe087a000\n"
        ".word 0xe59d06e8\n"
        ".word 0xe3500000\n"
        ".word 0x0a0000fa\n"
        ".word 0xe59d063c\n"
        ".word 0xeb02b6fe\n"
        ".word 0xe2801c01\n"
        ".word 0xe28110a7\n"
        ".word 0xe3a00024\n"
        ".word 0xeb03381c\n"
        ".word 0xe1a07000\n"
        ".word 0xe2840024\n"
        ".word 0xed900a08\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xeb033826\n"
        ".word 0xe1d700fa\n"
        ".word 0xe3a08079\n"
        ".word 0xe3a02f66\n"
        ".word 0xe0800006\n"
        ".word 0xe88d0101\n"
        ".word 0xe1d700f8\n"
        ".word 0xe3a01024\n"
        ".word 0xe0803005\n"
        ".word 0xe3a00002\n"
        ".word 0xeb033770\n"
        ".word 0xe1d700fa\n"
        ".word 0xe2882e12\n"
        ".word 0xe3a01024\n"
        ".word 0xe0800006\n"
        ".word 0xe88d0101\n"
        ".word 0xe1d700f8\n"
        ".word 0xe0803005\n"
        ".word 0xe3a00002\n"
        ".word 0xeb033767\n"
        ".word 0xe1d700fa\n"
        ".word 0xe59f22b8\n"
        ".word 0xe3a01024\n"
        ".word 0xe0800006\n"
        ".word 0xe88d0101\n"
        ".word 0xe1d700f8\n"
        ".word 0xe0803005\n"
        ".word 0xe3a00002\n"
        ".word 0xeb03375e\n"
        ".word 0xeeb00a48\n"
        ".word 0xe320f000\n"
        ".word 0xeb033807\n"
        ".word 0xe1d700fa\n"
        ".word 0xe3a0807e\n"
        ".word 0xe59f2288\n"
        ".word 0xe0800006\n"
        ".word 0xe88d0101\n"
        ".word 0xe1d700f8\n"
        ".word 0xe3a01024\n"
        ".word 0xe0803005\n"
        ".word 0xe3a00002\n"
        ".word 0xeb033751\n"
        ".word 0xe59d063c\n"
        ".word 0xe320f000\n"
        ".word 0xeb02b6c8\n"
        ".word 0xe0840080\n"
        ".word 0xe2800b01\n"
        ".word 0xe1d003f8\n"
        ".word 0xeb02b071\n"
        ".word 0xe3500001\n"
        ".word 0x13500002\n"
        ".word 0x13500006\n"
        ".word 0xe1d700fa\n"
        ".word 0xe0800006\n"
        ".word 0xe88d0101\n"
        ".word 0xe1d700f8\n"
        ".word 0xe0803005\n"
        ".word 0x0a0000d6\n"
        ".word 0xe3a02f67\n"
        ".word 0xe3a01024\n"
        ".word 0xe3a00002\n"
        ".word 0xeb03373d\n"
        ".word 0xe3a01f67\n"
        ".word 0xe3a00024\n"
        ".word 0xeb0337d6\n"
        ".word 0xe1a09000\n"
        ".word 0xe51f0564\n"
        ".word 0xe5901000\n"
        ".word 0xe3a00003\n"
        ".word 0xe2818a01\n"
        ".word 0xe2888fc3\n"
        ".word 0xe5981000\n"
        ".word 0xe0882101\n"
        ".word 0xe5921008\n"
        ".word 0xe5820008\n"
        ".word 0xe5d82018\n"
        ".word 0xe3520000\n"
        ".word 0x03510003\n"
        ".word 0x0a000002\n"
        ".word 0xe598101c\n"
        ".word 0xe12fff31\n"
        ".word 0xe5c8b018\n"
        ".word 0xe3a00001\n"
        ".word 0xe58d0000\n"
        ".word 0xe599000c\n"
        ".word 0xe1d710fa\n"
        ".word 0xe1d9c0fa\n"
        ".word 0xe1d990f8\n"
        ".word 0xe1d780f8\n"
        ".word 0xe1d030f2\n"
        ".word 0xe1d020f0\n"
        ".word 0xe081000c\n"
        ".word 0xe088c009\n"
        ".word 0xe0801006\n"
        ".word 0xe08c0005\n"
        ".word 0xeb02a309\n"
        ".word 0xe28400b0\n"
        ".word 0xe320f000\n"
        ".word 0xeb0335dc\n"
        ".word 0xe1d710fa\n"
        ".word 0xe0800006\n"
        ".word 0xe0808001\n"
        ".word 0xe28400b0\n"
        ".word 0xeb0335da\n"
        ".word 0xe1d710f8\n"
        ".word 0xe0800005\n"
        ".word 0xe3a09083\n"
        ".word 0xe0803001\n"
        ".word 0xe59f2164\n"
        ".word 0xe3a01024\n"
        ".word 0xe3a00002\n"
        ".word 0xe1cd80f0\n"
        ".word 0xeb03370a\n"
        ".word 0xe51f0620\n"
        ".word 0xe5901000\n"
        ".word 0xe3a00000\n"
        ".word 0xe2818a01\n"
        ".word 0xe2888fc3\n"
        ".word 0xe5981000\n"
        ".word 0xe0882101\n"
        ".word 0xe5921008\n"
        ".word 0xe5820008\n"
        ".word 0xe5d82018\n"
        ".word 0xe3520000\n"
        ".word 0x03510000\n"
        ".word 0x0a000002\n"
        ".word 0xe598101c\n"
        ".word 0xe12fff31\n"
        ".word 0xe5c8b018\n"
        ".word 0xe1d700fa\n"
        ".word 0xe59f2110\n"
        ".word 0xe3a01024\n"
        ".word 0xe0800006\n"
        ".word 0xe88d0201\n"
        ".word 0xe1d700f8\n"
        ".word 0xe0803005\n"
        ".word 0xe3a00002\n"
        ".word 0xeb0336f1\n"
        ".word 0xe1d700fa\n"
        ".word 0xe3a02e1a\n"
        ".word 0xe3a01024\n"
        ".word 0xe0800006\n"
        ".word 0xe88d0201\n"
        ".word 0xe1d700f8\n"
        ".word 0xe0803005\n"
        ".word 0xe3a00002\n"
        ".word 0xeb0336e8\n"
        ".word 0xe084008a\n"
        ".word 0xe2808a09\n"
        ".word 0xe59d0028\n"
        ".word 0xe1d822b0\n"
        ".word 0xe3e09000\n"
        ".word 0xe3a01008\n"
        ".word 0xeb02ade9\n"
        ".word 0xe3500000\n"
        ".word 0x159f90b0\n"
        ".word 0xe1d802b0\n"
        ".word 0xeb032dc1\n"
        ".word 0xe1a02000\n"
        ".word 0xe28dad19\n"
        ".word 0xe28f10a0\n"
        ".word 0xe1a0000a\n"
        ".word 0xfa0333bf\n"
        ".word 0xe59f1098\n"
        ".word 0xe3a00024\n"
        ".word 0xeb033771\n"
        ".word 0xe1d710fa\n"
        ".word 0xe1d020fa\n"
        ".word 0xe1d0c0f8\n"
        ".word 0xe1d730f8\n"
        ".word 0xe0810002\n"
        ".word 0xe0800006\n"
        ".word 0xe083100c\n"
        ".word 0xe0811005\n"
        ".word 0xee000a90\n"
        ".word 0xee001a10\n"
        ".word 0xeeb01a49\n"
        ".word 0xeeb02a48\n"
        ".word 0xe1a0200a\n"
        ".word 0xe1a01009\n"
        ".word 0xeef80ae0\n"
        ".word 0xeeb80ac0\n"
        ".word 0xeef01a41\n"
        ".word 0xe3a00003\n"
        ".word 0xeb033389\n"
        ".word 0xe59f1044\n"
        ".word 0xe3a00024\n"
        ".word 0xeb03375b\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xea00000d\n"
        ".word 0x323232ff\n"
        ".word 0x0000018e\n"
        ".word 0x0000018f\n"
        ".word 0x00000191\n"
        ".word 0x00000192\n"
        ".word 0x00006425\n"
        ".word 0x0000019a\n"
        ".word 0x0000019b\n"
        ".word 0x0000019e\n"
        ".word 0x0000019f\n"
        ".word 0x008400ff\n"
        ".word 0x00007325\n"
        ".word 0x000001a2\n"
        ".word 0x000001a1\n"
        ".word 0xe58db000\n"
        ".word 0xe58db004\n"
        ".word 0xe1d710fa\n"
        ".word 0xe1d020fa\n"
        ".word 0xe1d730f8\n"
        ".word 0xe1d0c0f8\n"
        ".word 0xe0822001\n"
        ".word 0xe1d802f0\n"
        ".word 0xe083100c\n"
        ".word 0xe0822006\n"
        ".word 0xe0811005\n"
        ".word 0xe3a0308d\n"
        ".word 0xeb031566\n"
        ".word 0xe59f10f0\n"
        ".word 0xe3a00024\n"
        ".word 0xeb03373a\n"
        ".word 0xe1a09000\n"
        ".word 0xe1d802b0\n"
        ".word 0xeb02a473\n"
        ".word 0xe24f3078\n"
        ".word 0xe3a0208d\n"
        ".word 0xe3a01004\n"
        ".word 0xe58d000c\n"
        ".word 0xe88d000e\n"
        ".word 0xe1d700fa\n"
        ".word 0xe1d920fa\n"
        ".word 0xe1d710f8\n"
        ".word 0xe1d930f8\n"
        ".word 0xe0822000\n"
        ".word 0xe0822006\n"
        ".word 0xe0810003\n"
        ".word 0xe0801005\n"
        ".word 0xe3a03001\n"
        ".word 0xe1a00003\n"
        ".word 0xeb0331ce\n"
        ".word 0xe2840b01\n"
        ".word 0xe28d7024\n"
        ".word 0xe1d027f2\n"
        ".word 0xe1d017f4\n"
        ".word 0xe3a0c097\n"
        ".word 0xe58d2020\n"
        ".word 0xe58db02c\n"
        ".word 0xe8871002\n"
        ".word 0xe3a02028\n"
        ".word 0xe1d007f6\n"
        ".word 0xe3a0702b\n"
        ".word 0xe3a0802a\n"
        ".word 0xe28d9014\n"
        ".word 0xe58d001c\n"
        ".word 0xe58d2010\n"
        ".word 0xe3a03029\n"
        ".word 0xe3a01027\n"
        ".word 0xe58d7004\n"
        ".word 0xe58d8000\n"
        ".word 0xe889000a\n"
        ".word 0xe28d0008\n"
        ".word 0xe3a0c026\n"
        ".word 0xe3a0402c\n"
        ".word 0xe8801010\n"
        ".word 0xe3a03024\n"
        ".word 0xe59d063c\n"
        ".word 0xe1a02006\n"
        ".word 0xe1a01005\n"
        ".word 0xeb027c64\n"
        ".word 0xe28dde6a\n"
        ".word 0xecbd8b04\n"
        ".word 0xe28dd010\n"
        ".word 0xe8bd9ff0\n"
        ".word 0xe59f2018\n"
        ".word 0xe3a01024\n"
        ".word 0xe3a00002\n"
        ".word 0xeb033666\n"
        ".word 0xe320f000\n"
        ".word 0xe320f000\n"
        ".word 0xeaffff25\n"
        ".word 0x000001a6\n"
        ".word 0x0000019d\n"
    );
}
#if 0
// Original partial readable draft retained for reconstruction; not compiled.
void ui_func_001f0454(s32 x, s32 y, s32 mode, s32 flag, s32 has_target,
                      s32 slide_dir) {
    CampFusionView* work = static_cast<CampFusionView*>(Camp_GetMainWork());
    if (work == nullptr) {                                  // 0x001F0468
        return;
    }

    const s32 slide_offset = (work->field_3fc / 4) % 3;     // 0x001F062C..0x001F0658
    bool fade_latched = false;                              // [sp+0x690]

    // 0x001F046C..0x001F0568: fixed frame panels.
    UiSprite_DrawPanel(2, 0x24, 1, x, y, 0x65);
    UiSprite_DrawNode(2, 0x24, 0x163, x, y, 0x6A);
    UiSprite_DrawNode(2, 0x24, 0x164, x, y, 0x6A);
    UiSprite_DrawNode(2, 0x24, 0x165, x, y, 0x6F);
    UiSprite_DrawNode(2, 0x24, 0x166, x, y, 0x6A);
    UiSprite_DrawNode(2, 0x24, 0x167, x, y, 0x6F);
    UiSprite_DrawNode(2, 0x24, 0x16A, x, y, 0x6A);   // 0x001F0524
    UiSprite_DrawNode(2, 0x24, 0x16B, x, y, 0x6F);
    UiSprite_DrawNode(2, 0x24, 0x16C, x, y, 0x74);

    // 0x001F056C..0x001F0628: "INHERITING" / "Parent Skills".
    char text[0x100];
    const Npc2dLayoutNode* node = LayoutNode(0x24, 0x168);
    UiFont_FormatString(text, "%s", kFusionTitleA);
    UiFont_DrawText(3, 0xFFu, text,
                    static_cast<f32>(x + node->x),
                    static_cast<f32>(y + node->y),
                    0.0f, 0.0f, 1.0f);
    node = LayoutNode(0x24, 0x169);
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
    node = LayoutNode(0x24, 0x4D);
    UiFont_FormatString(text, "%s",
                        Item_GetShortNameString(*reinterpret_cast<u16*>(row)));
    UiFont_DrawText(2, 0xFFFFFFFFu, text,
                    static_cast<f32>(x + node->x),
                    static_cast<f32>(y + node->y),
                    0.0f, 0.0f, 1.0f);
    node = LayoutNode(0x24, 0x4E);
    UiFont_FormatString(text, "%s",
                        Item_GetDescriptionString(*reinterpret_cast<u16*>(row), 0));
    UiFont_DrawText(2, 0xF49800FFu, text,
                    static_cast<f32>(x + node->x),
                    static_cast<f32>(y + node->y),
                    0.0f, 0.0f, 1.0f);
    node = LayoutNode(0x24, 0x51);

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
    node = LayoutNode(0x24, 0x1ED);
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
    for (s32 i = 0; i < 8; ++i) {
        s32 row_x = x;                                      // 0x001F09B8
        s32 row_y = y;                                      // 0x001F09B4
        f32 fade = 1.0f;                                    // 0x001F09AC
        node = LayoutNode(0x24, 0x17D + i);
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
                LayoutNode(0x24, 0x178);              // 0x001F0E38
            UiFont_DrawText(2, color, text,
                            static_cast<f32>(row_x + node->x + name_node->x),
                            static_cast<f32>(row_y + node->y + name_node->y),
                            0.0f, 0.0f, fade);              // 0x001F0E8C
            const Npc2dLayoutNode* icon_node =
                LayoutNode(0x24, 0x177);              // 0x001F0E90
            UiParty_DrawDemonBars(
                static_cast<s16>(work->rows_9010[i]),
                row_x + node->x + icon_node->x,
                row_y + node->y + icon_node->y, 0x74, 0, 0);
            const Npc2dLayoutNode* id_node =
                LayoutNode(0x24, 0x17C);              // 0x001F0ED4
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
                LayoutNode(0x24, 0x178);
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
                    GpuModeSlotSet(0x2AC, static_cast<u32>(
                        reinterpret_cast<std::uintptr_t>(
                            UiGpu_SetRenderMode(6, 1, 0)))); // 0x001F101C
                    UiSprite_DrawNode(2, 0x24, 0x173,
                                      row_x + node->x, row_y + node->y, 0x65);
                    GpuModeSlotSet(0x2AC, static_cast<u32>(
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
            node = LayoutNode(0x24, 0x193 + i);       // 0x001F1298
            UiSprite_DrawNode(2, 0x24, 0x18E, x + node->x, y + node->y, 0x65);
            UiSprite_DrawNode(2, 0x24, 0x18F, x + node->x, y + node->y, 0x65);
            UiSprite_DrawNode(2, 0x24, 0x190, x + node->x, y + node->y, 0x65);
            UiSprite_DrawNode(2, 0x24, 0x191, x + node->x, y + node->y, 0x6A);
            const Npc2dLayoutNode* pair_node =
                LayoutNode(0x24, 0x192);              // 0x001F1340
            UiParty_DrawDemonBars(static_cast<s16>(pairs.values[i]),
                                  x + node->x + pair_node->x,
                                  y + node->y + pair_node->y,
                                  0x6F, 0, 0);
        }
    } else {
        // 0x001F1164..0x001F128C
        node = LayoutNode(0x24, 0x197);
        UiSprite_DrawNode(2, 0x24, 0x16F, x + node->x, y + node->y, 0x65);
        UiSprite_DrawNode(2, 0x24, 0x170, x + node->x, y + node->y, 0x65);
        UiSprite_DrawNode(2, 0x24, 0x171, x + node->x, y + node->y, 0x65); // 0x001F11C4
        const Npc2dLayoutNode* money_node =
            LayoutNode(0x24, 0x178);                  // 0x001F11E4
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
        node = LayoutNode(0x24, 0x185 + i);           // 0x001F13C4
        UiSprite_DrawNode(2, 0x24, 0x16F, x + node->x, y + node->y, 0x65);
        UiSprite_DrawNode(2, 0x24, 0x170, x + node->x, y + node->y, 0x65);
        UiSprite_DrawNode(2, 0x24, 0x171, x + node->x, y + node->y, 0x65);

        if (UiList_CountActiveRows(party_list) > i) {       // 0x001F1450
            UiSprite_DrawNode(2, 0x24, 0x174, x + node->x, y + node->y, 0x6A);
            UiSprite_DrawNode(2, 0x24, 0x175, x + node->x, y + node->y, 0x6A);
            UiSprite_DrawNode(2, 0x24, 0x176, x + node->x, y + node->y, 0x6F);
            const u16 entry = work->rows_9020[lower_scroll + i];
            const u32 color =
                UiArray_ContainsU16(work->rows_9010, 8, entry) != 0
                    ? 0x008400FFu : 0xFFFFFFFFu;            // 0x001F14F8..0x001F1504
            UiFont_FormatString(text, "%s", Item_GetNameString(entry));
            const Npc2dLayoutNode* name_node =
                LayoutNode(0x24, 0x178);              // 0x001F151C
            UiFont_DrawText(2, color, text,
                            static_cast<f32>(x + node->x + name_node->x),
                            static_cast<f32>(y + node->y + name_node->y),
                            0.0f, 0.0f, 1.0f);              // 0x001F1570
            const Npc2dLayoutNode* icon_node =
                LayoutNode(0x24, 0x177);              // 0x001F1574
            UiParty_DrawDemonBars(static_cast<s16>(entry),
                                  x + node->x + icon_node->x,
                                  y + node->y + icon_node->y,
                                  0x74, 0, 0);
            const Npc2dLayoutNode* id_node =
                LayoutNode(0x24, 0x17C);              // 0x001F15B4
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
        node = LayoutNode(0x24, 0x1A7 +
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
            LayoutNode(0x24, 0x19C);                  // 0x001F1768
        const s16* rect = reinterpret_cast<const s16*>(panel_node->extra);
        GpuModeSlotSet(0x30C, 3);                                  // 0x001F1780
        const Npc2dLayoutNode* detail_node =
            LayoutNode(0x24, 0x1A7 +
                             UiListCursor_GetSelectedRow(cursor));
        UiScissor_SetRect(x + detail_node->x + panel_node->x,
                          y + detail_node->y + panel_node->y,
                          rect[0], rect[1], 1);             // 0x001F17EC
        const s32 panel19e_x = x + UiAnimSprite_GetPosX(&work->sprite_0b0) +
                               panel_node->x;            // 0x001F17F8..0x001F181C
        const s32 panel19e_y = y + UiAnimSprite_GetPosY(&work->sprite_0b0) +
                               panel_node->y;
        UiSprite_DrawNode(2, 0x24, 0x19E, panel19e_x, panel19e_y, 0x83); // 0x001F1830
        GpuModeSlotSet(0x30C, 0);                                  // 0x001F183C

        node = panel_node;                                  // r7 := node 0x19C
        UiSprite_DrawNode(2, 0x24, 0x19F, x + node->x, y + node->y, 0x83);
        UiSprite_DrawNode(2, 0x24, 0x1A0, x + node->x, y + node->y, 0x83);

        const u16 entry = work->rows_9020[lower_selected];
        const u32 color = UiArray_ContainsU16(work->rows_9010, 8, entry) != 0
                              ? 0x008400FFu : 0xFFFFFFFFu; // 0x001F18D4..0x001F18DC
        UiFont_FormatString(text, "%s", Item_GetNameString(entry));
        const Npc2dLayoutNode* name_node =
            LayoutNode(0x24, 0x1A2);                  // 0x001F1904
        UiFont_DrawText(3, color, text,
                        static_cast<f32>(x + node->x + name_node->x),
                        static_cast<f32>(y + node->y + name_node->y),
                        0.0f, 0.0f, 1.0f);                  // 0x001F1950
        const Npc2dLayoutNode* icon_node =
            LayoutNode(0x24, 0x1A1);                  // 0x001F1958
        UiParty_DrawDemonBars(static_cast<s16>(entry),
                              x + node->x + icon_node->x,
                              y + node->y + icon_node->y,
                              0x8D, 0, 0);
        const Npc2dLayoutNode* id_node =
            LayoutNode(0x24, 0x1A6);                  // 0x001F19DC
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
                     work->field_476, work->field_472, work->field_474,
                     0x97, 0);
    (void)slide_dir;
}
#endif

} // namespace smt4::ui
