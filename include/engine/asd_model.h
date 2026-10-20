#pragma once
#include <cstddef>
#include "types.h"

namespace smt4::engine {

/**
 * Resolved Atlus AsdSDK model data block (`AsdModelData`).
 *
 * Only the offsets actually touched by the ten reconstructed AsdModel /
 * EffectEditor functions are named. Every field below is backed by an
 * `LDR/STR [reg, #imm]` in `tools/split_asm.py` output.
 *
 * Original Atlus source path:
 * `c:\SMT4\XRD686\AsdSDK\Source\Gfx\Model\AsdModel.cpp`
 */
struct AsdModelData {
    u8  pad_00[0x1C];                   // +0x0000..+0x001C
    u32 node_count;                     // +0x001C: `ldr r1,[r0,#0x1c]` (0x002a9c00 / 0x0031dcb8)
    u32 node_list_rel;                  // +0x0020: relative pointer, `ldr r1,[r0,#0x20]!` (0x002a9c40)
    u8  pad_24[0x04];                   // +0x0024..+0x0028
    void* node_grid;                    // +0x0028: grid container used by 0x00192594 / 0x002a94e8
    u8  pad_2c[0x38];                   // +0x002C..+0x0064
    u32 mesh_count;                     // +0x0064: `ldr r0,[r0,#0x64]` (0x002a951c)
    u32 mesh_list_rel;                  // +0x0068: `ldr r2,[r0,#0x68]!` (0x002a9578)
    u32 controller_count;               // +0x006C: `ldr r0,[r0,#0x6c]` (0x002a96c0)
    u32 controller_list_rel;            // +0x0070: `ldr r2,[r0,#0x70]!` (0x002a9718)
    u32 draw_count;                     // +0x0074: `ldr r0,[r0,#0x74]` (0x002a9864)
    u32 draw_list_rel;                  // +0x0078: `ldr r2,[r0,#0x78]!` (0x002a990c)
    u8  pad_7c[0x64];                   // +0x007C..+0x00E0
    u32 subnode_list_rel;               // +0x00E0: `ldr r1,[r0,#0xe0]!` (0x002a9eac)
    u8  pad_e4[0x40];                   // +0x00E4..+0x0124
    u8  pad_124[0x24];                  // +0x0124..+0x0148 (no proven field)
    void* field_148;                    // +0x0148: `ldr r7,[r6,#0x148]` (0x002a9768)
    s32 field_14c;                      // +0x014C: effective `ldr r1,[r6,#0x124]` after `ldr r0,[r6,#0x28]!` (0x002a9820)
    void* field_150;                    // +0x0150: `ldr r7,[r6,#0x150]` (0x002a995c)
    s32 field_154;                      // +0x0154: effective `ldr r3,[r6,#0x12c]` after `ldr r0,[r6,#0x28]!` (0x002a9a14)
    u8  pad_158[0xd0];                  // +0x0158..+0x0228
    u32 field_228;                      // +0x0228: `ldr r1,[r0,#0x228]` (0x002a9608)
    s32 field_22c;                      // +0x022C: `ldr r0,[r0,#0x22c]` (0x002a963c)
    u8  pad_230;                        // +0x0230
    u8  field_231;                      // +0x0231: `ldrb r1,[r0,#0x231]` (0x002a9618)
};
static_assert(offsetof(AsdModelData, node_count) == 0x1C);
static_assert(offsetof(AsdModelData, node_grid) == 0x28);
static_assert(offsetof(AsdModelData, mesh_count) == 0x64);
static_assert(offsetof(AsdModelData, controller_count) == 0x6C);
static_assert(offsetof(AsdModelData, draw_count) == 0x74);
static_assert(offsetof(AsdModelData, subnode_list_rel) == 0xE0);
static_assert(offsetof(AsdModelData, field_148) == 0x148);
static_assert(offsetof(AsdModelData, field_14c) == 0x14C);
static_assert(offsetof(AsdModelData, field_150) == 0x150);
static_assert(offsetof(AsdModelData, field_154) == 0x154);
static_assert(offsetof(AsdModelData, field_228) == 0x228);
static_assert(offsetof(AsdModelData, field_22c) == 0x22C);
static_assert(offsetof(AsdModelData, field_231) == 0x231);

/**
 * AsdModel instance (0xA8 bytes), allocated by AsdModel_func_001fe470.
 *
 * Layout proven by `LDR/STR` accesses in 0x001fe470, 0x0014515c,
 * 0x0014ec68, 0x00192594, 0x002a94e8 and 0x002a5a54.
 */
struct AsdModel {
    u32 flags;                          // +0x00: `orr r1,r1,#2; str r1,[r4]` (0x001926ac)
    void* source;                       // +0x04: model source handle, refcount at +0, ATBC at +0xC
    u32 field_08;                       // +0x08: `stm r5,{r1,r3}` with r3=7 (0x001fe4c0)
    s32 field_0c;                       // +0x0C: initialized to -1 (0x001fe4ac)
    s32 field_10;                       // +0x10: initialized to -1 (0x001fe4b4)
    u8  pad_14[0x08];                   // +0x14..+0x1C
    u16 field_1c[3];                    // +0x1C: name->index map, 0xFFFF-filled by 0x001524d0
    u8  pad_22[0x02];                   // +0x22..+0x24
    void** node_handles;                // +0x24: array of created node objects (0x00192708)
    s32 node_handle_count;              // +0x28: set to 1 (0x001926e4)
    void* model_data;                   // +0x2C: `str r0,[r4,#0x2c]` (0x00192640)
    void** node_ptrs;                   // +0x30: `str r0,[r4,#0x30]` (0x002a9560)
    s32 node_count;                     // +0x34: `str r0,[r4,#0x34]` (0x002a9524)
    s32 current_node;                   // +0x38: `str r5,[r6,#0x38]` (0x002a5b8c)
    s32 max_node_index;                 // +0x3C: `str r5,[r4,#0x3c]` (0x002a95cc)
    u8  pad_40[0x08];                   // +0x40..+0x48
    void* anim_controller;              // +0x48: `str r0,[r4,#0x48]` (0x002a95d4)
    void* anim_controller_alt;          // +0x4C: `str r0,[r4,#0x4c]` (0x002a95f0)
    u32 field_50;                       // +0x50: `str r1,[r6,#0x50]` (0x002a5b0c)
    void** mesh_ptrs;                   // +0x54: `str r0,[r4,#0x54]` (0x002a9704)
    s32 mesh_count;                     // +0x58: `str r0,[r4,#0x58]` (0x002a96c8)
    s32 field_5c;                       // +0x5C: `str r5,[r4,#0x5c]` (0x002a9a98)
    void* mesh_controller;              // +0x60: `str r5,[r4,#0x60]` (0x002a9858)
    void** controller_ptrs;             // +0x64: `str r0,[r4,#0x64]` (0x002a98f8)
    s32 controller_count;               // +0x68: `str r0,[r4,#0x68]` (0x002a986c)
    u8  pad_6c[0x04];                   // +0x6C..+0x70
    void* draw_controller;              // +0x70: `str r5,[r4,#0x70]` (0x002a9a4c)
    f32 field_74;                       // +0x74: 1.0f (0x001fe4fc)
    f32 field_78;                       // +0x78: 1.0f (0x001fe500 / 0x002a5a6c)
    f32 field_7c;                       // +0x7C: 1.0f (0x001fe504 / 0x002a9a64)
    f32 field_80;                       // +0x80: 1.0f (0x001fe508)
    f32 field_84;                       // +0x84: 0.0f (0x001fe524)
    f32 field_88;                       // +0x88: 0.0f (0x001fe51c)
    f32 field_8c;                       // +0x8C: 0.0f (0x001fe518)
    u8  field_90;                       // +0x90: `strb r1,[r4,#0x90]` (0x001fe50c)
    u8  pad_91[0x03];                   // +0x91..+0x94
    s32 atbc_chunk_count;               // +0x94: `str r5,[fp]` (0x00145190)
    s32 atbc_key_count;                 // +0x98: `str sl,[r8]` (0x00145268)
    void* atbc_keys;                    // +0x9C: `str r0,[r8,#4]` (0x001452a4)
    s32 effect_part_count;              // +0xA0: `ldr r0,[r0,#0xa0]` (0x0014ec74)
    void* effect_parts;                 // +0xA4: `ldr r0,[r6,#0xa4]` (0x0014ec88)
};
static_assert(offsetof(AsdModel, flags) == 0x00);
static_assert(offsetof(AsdModel, source) == 0x04);
static_assert(offsetof(AsdModel, field_1c) == 0x1C);
static_assert(offsetof(AsdModel, node_handles) == 0x24);
static_assert(offsetof(AsdModel, model_data) == 0x2C);
static_assert(offsetof(AsdModel, node_ptrs) == 0x30);
static_assert(offsetof(AsdModel, node_count) == 0x34);
static_assert(offsetof(AsdModel, max_node_index) == 0x3C);
static_assert(offsetof(AsdModel, anim_controller) == 0x48);
static_assert(offsetof(AsdModel, atbc_chunk_count) == 0x94);
static_assert(offsetof(AsdModel, effect_parts) == 0xA4);
static_assert(sizeof(AsdModel) == 0xA8);

/**
 * Thin view object whose first word points at an AsdModelData block.
 * `engine_func_003170b8` allocates exactly 4 bytes and stores the source
 * model there before calling AsdModel_func_0031dc4c.
 */
struct AsdModelView {
    AsdModelData* data;                 // +0x00: `ldr r0,[sl]` (0x0031dcb4)
};
static_assert(sizeof(AsdModelView) == 0x04);


/**
 * Result of AsdModel_func_0031dc4c (0x28 bytes), completed by its caller
 * with the view/source pair at +0x20/+0x24 (0x00317190).
 */
struct AsdModelNodeSet {
    void** node_handles;                // +0x00: `str r0,[r4]` (0x0031dce4)
    u32 node_count;                     // +0x04: `str r0,[r4,#4]` (0x0031dcbc)
    void** mesh_handles;                // +0x08: `str r0,[r4,#8]` (0x0031def0)
    u32 mesh_count;                     // +0x0C: `str r0,[r4,#0xc]` (0x0031deb4)
    void** mesh_handles_alt;            // +0x10: `str r0,[r4,#0x10]` (0x0031df24)
    void** draw_handles;                // +0x14: `str r0,[r4,#0x14]` (0x0031e0a4)
    u32 draw_count;                     // +0x18: `str r0,[r4,#0x18]` (0x0031e068)
    void** draw_handles_alt;            // +0x1C: `str r0,[r4,#0x1c]` (0x0031e0d8)
    void* view;                         // +0x20: set by caller 0x00317194
    void* source;                       // +0x24: set by caller 0x00317194
};
static_assert(offsetof(AsdModelNodeSet, mesh_count) == 0x0C);
static_assert(offsetof(AsdModelNodeSet, draw_count) == 0x18);
static_assert(offsetof(AsdModelNodeSet, view) == 0x20);
static_assert(sizeof(AsdModelNodeSet) == 0x28);

/**
 * Process-wide AsdModel manager (`g_AsdModelManager`, 0x00464AF0).
 * Counters/flags proven by 0x0010495c, 0x00192594, 0x001fe470,
 * 0x002a9acc, 0x002b2b78.
 */
struct AsdModelManager {
    u8  flag_00;                        // +0x00
    u8  flag_01;                        // +0x01: `strb r6,[r8,#1]` (0x00104970)
    u8  pad_02[0x01];                   // +0x02
    u8  flag_03;                        // +0x03: `ldrb r0,[r1,#3]` (0x002a9f64)
    u8  pad_04[0x34];                   // +0x04..+0x38
    u32 ref_count_38;                   // +0x38: 0x002b2c3c
    u32 ref_count_3c;                   // +0x3C: 0x001fe534
    u32 ref_count_40;                   // +0x40: 0x001926bc
    u8  pad_44[0x10];                   // +0x44..+0x54
    void* shadow_model;                 // +0x54: `str r0,[r8,#0x54]` (0x00104ad8)
    u8  pad_58[0x14];                   // +0x58..+0x6C
    void* shadow_model_resource;        // +0x6C: `str r0,[r8,#0x6c]` (0x00104988)
    u8  pad_70[0x0C];                   // +0x70..+0x7C
    void* field_7c;                     // +0x7C: `ldr r4,[r0,#0x7c]` (0x002a9bb4)
};
static_assert(offsetof(AsdModelManager, flag_01) == 0x01);
static_assert(offsetof(AsdModelManager, ref_count_38) == 0x38);
static_assert(offsetof(AsdModelManager, ref_count_40) == 0x40);
static_assert(offsetof(AsdModelManager, shadow_model) == 0x54);
static_assert(offsetof(AsdModelManager, shadow_model_resource) == 0x6C);
static_assert(offsetof(AsdModelManager, field_7c) == 0x7C);

extern AsdModelManager g_AsdModelManager;   // 0x00464AF0

/**
 * 28-byte animation-table signature object built by
 * AsdModel_func_002b2b78.
 */
struct AsdAnimTable {
    u32 field_00;                       // +0x00: `str r5,[r0]` with r5=1 (0x002b2bc4)
    u8  field_04;                       // +0x04: `strb r5,[r0,#4]` (0x002b2bc8)
    u8  pad_05[0x03];                   // +0x05..+0x08
    void* signature;                    // +0x08: `str r0,[r4,#8]` (0x002b2bf8)
    void* atbc;                         // +0x0C: `str r6,[r0,#0xc]` (0x002b2bd4)
    void* chunk;                        // +0x10: `str r5,[r4,#0x10]` (0x002b2c28)
    void* owner;                        // +0x14: `streq r8,[r4,#0x14]` (0x002b2c30)
    u32 field_18;                       // +0x18: zeroed by constructor (0x002b2bc0)
};
static_assert(offsetof(AsdAnimTable, signature) == 0x08);
static_assert(offsetof(AsdAnimTable, chunk) == 0x10);
static_assert(offsetof(AsdAnimTable, owner) == 0x14);
static_assert(sizeof(AsdAnimTable) == 0x1C);

/**
 * Growable pointer array with a tagged capacity word
 * (`0x40000000` marks an empty inline capacity; see 0x002a9be4).
 */
struct AsdPtrVector {
    void* ctx;                          // +0x00: allocator/owner context
    void** begin;                       // +0x04
    void** end;                         // +0x08
    u32 capacity;                       // +0x0C: high bits are tags
};
static_assert(offsetof(AsdPtrVector, begin) == 0x04);
static_assert(offsetof(AsdPtrVector, capacity) == 0x0C);

/**
 * Entry of the global node-name table array at 0x00464B8C.
 * `+0x14` is a growable pointer vector (AsdPtrVector layout).
 */
struct AsdNodeNameTableEntry {
    u8  pad_00[0x0C];                   // +0x00..+0x0C
    void* field_0c;                     // +0x0C: `ldr r0,[r7,#0xc]` (0x002aa140)
    void* owner;                        // +0x10: copied into entry+0x0C (0x002aa1d4)
    AsdPtrVector vec;               // +0x14: vector base passed to 0x002af528
};
static_assert(offsetof(AsdNodeNameTableEntry, field_0c) == 0x0C);
static_assert(offsetof(AsdNodeNameTableEntry, owner) == 0x10);
static_assert(offsetof(AsdNodeNameTableEntry, vec) == 0x14);

// ---------------------------------------------------------------------------
// EffectEditor workspace (0x002fcd20)
// ---------------------------------------------------------------------------

/**
 * Effect-editor menu / draw command entry (0x18 bytes).
 * Every entry is written with the same six stores in 0x002fcd20:
 * name at +0x00, type byte at +0x04, callback A at +0x08,
 * callback B at +0x0C, payload at +0x10 and an f32 at +0x14.
 */
struct EffectEditorMenuEntry {
    const char* name;                   // +0x00
    u8  type;                           // +0x04
    u8  pad_05[0x03];                   // +0x05..+0x08
    void* callback_a;                   // +0x08
    void* callback_b;                   // +0x0C
    void* payload;                      // +0x10
    f32 value;                          // +0x14
};
static_assert(offsetof(EffectEditorMenuEntry, callback_a) == 0x08);
static_assert(offsetof(EffectEditorMenuEntry, payload) == 0x10);
static_assert(sizeof(EffectEditorMenuEntry) == 0x18);

/**
 * Editor effect-part record referenced through `parts_manager`
 * (`+0x80` list index, `+0x84` flag bits, `+0x90` element table,
 * `+0x98` flags, `+0x9C` name buffer).
 */
struct EffectEditorPart {
    u8  pad_00[0x80];                   // +0x00..+0x80
    s32 list_index;                     // +0x80: `ldr r4,[r0,#0x80]` (0x002fce88)
    u32 flags;                          // +0x84: `eor r1,r1,#2` (0x002fd02c)
    u8  pad_88[0x08];                   // +0x88..+0x90
    void* element_table;                // +0x90: `ldr r0,[r0,#0x90]` (0x002fd0dc)
    u8  pad_94[0x04];                   // +0x94..+0x98
    u32 field_98;                       // +0x98: `tst r1,#1` (0x002fd160)
    u8  name[0x28];                     // +0x9C: formatted into by 0x002be7fc
};
static_assert(offsetof(EffectEditorPart, list_index) == 0x80);
static_assert(offsetof(EffectEditorPart, flags) == 0x84);
static_assert(offsetof(EffectEditorPart, element_table) == 0x90);
static_assert(offsetof(EffectEditorPart, field_98) == 0x98);

/**
 * Effect-editor singleton (`g_EffectEditor`, 0x0044EA80).
 */
struct EffectEditorState {
    u8  flag_00;                        // +0x00: `ldrb r0,[r8]` (0x002fd870)
    u8  frame_counter;                  // +0x01: `strb r1,[r8,#1]` (0x002fda34)
    u8  pad_02[0x04];                   // +0x02..+0x06
    u8  flag_06;                        // +0x06: `strb r0,[r8,#6]` (0x002fd720)
    u8  flag_07;                        // +0x07: `ldrb r0,[r8,#7]` (0x002fd5e4)
    u8  flag_08;                        // +0x08: `strb r0,[r8,#8]` (0x002fd5fc)
    u8  speed_mode;                     // +0x09: 0=normal, 1=STOP, 2=SLOW (0x002fd690)
    u8  pad_0a[0x02];                   // +0x0A..+0x0C
    s32 list_offset;                    // +0x0C: `str r1,[r7,#0xc]` (0x002fcdf8)
    void* selected_part;                // +0x10: `str r0,[r8,#0x10]` (0x002fd840)
    void* parts;                        // +0x14: `str r0,[r7,#0x14]` (0x002fcd68)
    void* active_element;               // +0x18: `str r6,[r7,#0x18]` (0x00242770)
    void* element;                      // +0x1C: `str r0,[r7,#0x1c]` (0x0024273c)
    void* work_part;                    // +0x20: `str r0,[r8,#0x20]` (0x002fd7b8)
    void* part_track;                   // +0x24: `str r0,[r7,#0x24]` (0x002426ec)
    u8  pad_28[0x0C];                   // +0x28..+0x34
    void* menu_current;                 // +0x34: `str r0,[r8,#0x34]` (0x002fd524)
    void* menu_pending;                 // +0x38: `stmne r1,{r0,r4}` (0x002fd5d8); entry pointer
                                        //       `str r0,[r7,#0x38]` (0x00242778)
    u8  pad_3c[0x10];                   // +0x3C..+0x4C
    u32 field_4c;                       // +0x4C: `str sl,[r7,#0x4c]` (0x002426c0)
    u32 field_50;                       // +0x50: `str sl,[r7,#0x50]` (0x002426c8)
    u32 field_54;                       // +0x54: `stm r2,{r1,sl}` with r1=1 (0x002426cc)
    u32 field_58;                       // +0x58: same store, r5/sl = 0 (0x002426cc)
    u32 field_5c;                       // +0x5C: untouched here
    u32 field_60;                       // +0x60: `str sl,[r7,#0x60]` (0x002426d4)
    u32 field_64;                       // +0x64: `str sl,[r7,#0x64]` (0x002426d8)
    u32 field_68;                       // +0x68: `str sl,[r7,#0x68]` (0x002426dc)
    u8  pad_6c[0x14];                   // +0x6C..+0x80
    s32 timer;                          // +0x80: `str r0,[r8,#0x80]` (0x002fd954)
};
static_assert(offsetof(EffectEditorState, frame_counter) == 0x01);
static_assert(offsetof(EffectEditorState, speed_mode) == 0x09);
static_assert(offsetof(EffectEditorState, list_offset) == 0x0C);
static_assert(offsetof(EffectEditorState, selected_part) == 0x10);
static_assert(offsetof(EffectEditorState, parts) == 0x14);
static_assert(offsetof(EffectEditorState, active_element) == 0x18);
static_assert(offsetof(EffectEditorState, element) == 0x1C);
static_assert(offsetof(EffectEditorState, work_part) == 0x20);
static_assert(offsetof(EffectEditorState, part_track) == 0x24);
static_assert(offsetof(EffectEditorState, menu_current) == 0x34);
static_assert(offsetof(EffectEditorState, menu_pending) == 0x38);
static_assert(offsetof(EffectEditorState, field_4c) == 0x4C);
static_assert(offsetof(EffectEditorState, field_54) == 0x54);
static_assert(offsetof(EffectEditorState, field_68) == 0x68);
static_assert(offsetof(EffectEditorState, timer) == 0x80);

/**
 * Foreground editor widget at 0x0044F858 (`AsdUi`-style object).
 * `+0x0C` mode, `+0x10` flags word, `+0x14` work-buffer base and `+0x18`
 * menu-entry count.  These two stores are made with r7 == 0x0044F858
 * (0x002fd4e4 / 0x002fd4e8), not with the g_EffectEditor base.
 *
 * The same layout is instantiated a second time at 0x0044F8C8, whose first
 * three words are filled by `EffectEditor_func_0024246c` (0x0024254C /
 * 0x00242554 / 0x00242578) and whose `+0x0C` is the menu cursor.
 */
struct EffectEditorWidget {
    void* owner;                        // +0x00: `str r1,[r0]` (0x00242578)
    u32 field_04;                       // +0x04: `str r2,[r0,#4]` (0x0024254c)
    u32 field_08;                       // +0x08: `str r1,[r0,#8]` (0x00242554)
    u32 mode;                           // +0x0C: `ldr r0,[r4,#0xc]` (0x002fcd94)
    u32 flags;                          // +0x10: `bic r0,r0,#1` (0x002fcd50)
    void* menu;                         // +0x14: `str r5,[r7,#0x14]` (0x002fd4e8)
    u32 menu_count;                     // +0x18: `str r0,[r7,#0x18]` (0x002fd4e4)
};
static_assert(offsetof(EffectEditorWidget, owner) == 0x00);
static_assert(offsetof(EffectEditorWidget, field_04) == 0x04);
static_assert(offsetof(EffectEditorWidget, field_08) == 0x08);
static_assert(offsetof(EffectEditorWidget, mode) == 0x0C);
static_assert(offsetof(EffectEditorWidget, flags) == 0x10);
static_assert(offsetof(EffectEditorWidget, menu) == 0x14);
static_assert(offsetof(EffectEditorWidget, menu_count) == 0x18);

extern EffectEditorState g_EffectEditor;    // 0x0044EA80

// ---------------------------------------------------------------------------
// Ledger entry points (address / size match config/functions.csv)
// ---------------------------------------------------------------------------

void AsdModel_func_0010495c();                                              // 0x0010495c, 1108 B
void AsdModel_func_0014515c(AsdModel* model, const void* atbc);             // 0x0014515c,  688 B
void AsdModel_func_0014ec68(AsdModel* model, s32 index);                    // 0x0014ec68,  792 B
void AsdModel_func_00192594(AsdModel* model, AsdModel* source, s32 mode);   // 0x00192594,  484 B
AsdModel* AsdModel_func_001fe470();                                         // 0x001fe470,  288 B
AsdModel* AsdModel_func_002a94e8(AsdModel* model);                          // 0x002a94e8, 1508 B
void AsdModel_func_002a9acc(AsdModelView* view, AsdModel* model,
                            u32 flags, AsdModel* source);                   // 0x002a9acc, 1880 B
AsdAnimTable* AsdModel_func_002b2b78(void* data, void* owner);              // 0x002b2b78,  340 B
AsdModelNodeSet* AsdModel_func_0031dc4c(AsdModelView* view);                // 0x0031dc4c, 2028 B
void* EffectEditor_func_002fcd20();                                         // 0x002fcd20, 4160 B

} // namespace smt4::engine
