#pragma once
#include <cstddef>
#include "types.h"

namespace smt4::engine {
struct AsdTexture;
}

namespace smt4::battle {

// ---------------------------------------------------------------------------
// EnemyDraw.cpp (0x0033EADC)
//
// Original Atlus source path:
//   c:\SMT4\XRD686\sdds4\program\battle\EnemyDraw\EnemyDraw.cpp
// ---------------------------------------------------------------------------

/** Draw-list header reached through `work->+0x10` (`ldr r0,[sb,#0x10]`). */
struct EnemyDrawHeader {
    u8  pad_00[0x0C];
    u16 count;                          // +0x0C: `ldrh r7,[r0,#0xc]` (0x0033ebb8)
    u8  pad_0E[4];                      // +0x0E..+0x12
    s16 field_12;                       // +0x12: `ldrsh r3,[r0,#0x12]` (0x0033ecc4)
    s16 field_14;                       // +0x14: `ldrsh r1,[r0,#0x14]` (0x0033ecbc)
    s16 field_16;                       // +0x16: `ldrsh r2,[r0,#0x16]` (0x0033ecc0)
    u8  pad_18[8];                      // +0x18..+0x20
};
static_assert(offsetof(EnemyDrawHeader, count) == 0x0C);
static_assert(offsetof(EnemyDrawHeader, field_12) == 0x12);
static_assert(offsetof(EnemyDrawHeader, field_14) == 0x14);
static_assert(offsetof(EnemyDrawHeader, field_16) == 0x16);

/** One 0x18-byte entry in the array at `EnemyDrawWork::+0x20`. */
struct EnemyDrawEntry {
    u32 index;                          // +0x00: `ldr sl,[r8]` (0x0033ed34)
    u32 field_04;                       // +0x04: `ldr r1,[r8,#4]` (0x0033ed38)
    f32 offset_x;                       // +0x08: `vldr s1,[r8,#8]` (0x0033f1ac)
    f32 offset_y;                       // +0x0C: `vldr s1,[r8,#0xc]` (0x0033f1c0)
    u8  pad_10[8];                      // +0x10..+0x18
};
static_assert(offsetof(EnemyDrawEntry, field_04) == 0x04);
static_assert(offsetof(EnemyDrawEntry, offset_x) == 0x08);
static_assert(offsetof(EnemyDrawEntry, offset_y) == 0x0C);
static_assert(sizeof(EnemyDrawEntry) == 0x18);

/** One 0x28-byte model/motion record in the array at `EnemyDrawWork::+0x18`. */
struct EnemyDrawUnit {
    u8  pad_00[0x10];                   // +0x00..+0x10
    f32 x;                              // +0x10: `vldr s0,[r6,#0x10]` (0x0033eeb0)
    f32 y;                              // +0x14: `vldr s3,[r6,#0x14]` (0x0033eec0)
    f32 width;                          // +0x18: `vldmia r0,{s1,s2}` with r0=r6+0x18
    f32 height;                         // +0x1C: second word of 0x0033eeb8
    u16 field_20;                       // +0x20: `ldrh r0,[r6,#0x20]` (0x0033efac)
    u8  field_22;                       // +0x22: `ldrb r1,[r6,#0x22]` (0x0033f280)
    u8  field_23;                       // +0x23: `ldrb r0,[r6,#0x23]` (0x0033ef20)
    u8  model_index;                    // +0x24: `ldrb r2,[r6,#0x24]` (0x0033eea4)
    u8  flag_25;                        // +0x25: `ldrb r1,[r6,#0x25]` (0x0033eddc)
    u8  mode_26;                        // +0x26: `ldrb r0,[r6,#0x26]` (0x0033f294)
    u8  flags_27;                       // +0x27: `ldrb r0,[r6,#0x27]` (0x0033eec4)
};
static_assert(offsetof(EnemyDrawUnit, x) == 0x10);
static_assert(offsetof(EnemyDrawUnit, field_20) == 0x20);
static_assert(offsetof(EnemyDrawUnit, model_index) == 0x24);
static_assert(offsetof(EnemyDrawUnit, flags_27) == 0x27);
static_assert(sizeof(EnemyDrawUnit) == 0x28);

/** 0x20-byte model-size table row (`[sb+0x14] + model*0x20`). */
struct EnemyDrawModelEntry {
    u8  pad_00[0x18];
    void* size_record;                  // +0x18: `ldr r1,[r1,#0x18]` (0x0033eebc)
    u8  pad_1c[4];                      // stride is 0x20 (`model_index * 0x20`)
};
static_assert(offsetof(EnemyDrawModelEntry, size_record) == 0x18);
static_assert(sizeof(EnemyDrawModelEntry) == 0x20);

/** Size record reached from `EnemyDrawModelEntry::size_record`. */
struct EnemyDrawModelSize {
    u8  pad_00[0x14];
    s32 width;                          // +0x14: `vldmia r1,{s1,s2}` with r1=record+0x14
    s32 height;                         // +0x18
};
static_assert(offsetof(EnemyDrawModelSize, width) == 0x14);

/** One 0x58-byte render record allocated at `work->+0x2C`. */
struct EnemyDrawRender {
    f32 position[12];                   // +0x00..+0x30: 12 `vstr` at 0x0033f1fc..0x0033f25c
    f32 matrix[8];                      // +0x30..+0x50: 8 `vstr` at 0x0033f260..0x0033f27c
    f32 alpha;                          // +0x50: `vstr s0,[r7,#0x50]` (0x0033f290)
    void* primitive;                    // +0x54: `str r0,[r7,#0x54]` (0x0033f2cc)
};
static_assert(offsetof(EnemyDrawRender, matrix) == 0x30);
static_assert(offsetof(EnemyDrawRender, alpha) == 0x50);
static_assert(offsetof(EnemyDrawRender, primitive) == 0x54);
static_assert(sizeof(EnemyDrawRender) == 0x58);

/** One 12-byte counter block at `work->+0x30` (6 u16 per enemy). */
struct EnemyDrawCounter {
    u32 field_00;                       // +0x00: `str r1,[r4,r3,lsl #2]` (0x0033ed58)
    u16 field_04;                       // +0x04: `strh r2,[r7,r6]` (0x0033ed74)
    u16 field_06;                       // +0x06: incremented at 0x0033edf0
    u16 field_08;                       // +0x08: incremented at 0x0033ee78
    u16 field_0A;                       // +0x0A: cleared by 0x0033eda8
};
static_assert(offsetof(EnemyDrawCounter, field_04) == 0x04);
static_assert(offsetof(EnemyDrawCounter, field_06) == 0x06);
static_assert(offsetof(EnemyDrawCounter, field_08) == 0x08);
static_assert(sizeof(EnemyDrawCounter) == 0x0C);

/** Workspace passed in r0 to `EnemyDraw_func_0033eadc`. */
struct EnemyDrawWork {
    u8  pad_00[8];                      // +0x00..+0x08
    u32 field_08;                       // +0x08: `ldr r0,[sb,#8]` (0x0033eb14)
    u32 field_0C;                       // +0x0C: `ldr r0,[sb,#0xc]` (0x0033eb3c)
    EnemyDrawHeader* header;            // +0x10: `ldr r0,[sb,#0x10]`
    EnemyDrawModelEntry* models;        // +0x14: `ldr r1,[sb,#0x14]` (0x0033eea8)
    EnemyDrawUnit* units;               // +0x18: `ldr r1,[sb,#0x18]` (0x0033edb4)
    const u16* index_array;             // +0x1C: `ldr ip,[sb,#0x1c]` (0x0033ed1c)
    EnemyDrawEntry* entries;            // +0x20: `ldr r1,[sb,#0x20]` (0x0033ed18)
    u8  pad_24[8];                      // +0x24..+0x2C
    EnemyDrawRender* records;           // +0x2C: `str r0,[sb,#0x2c]` (0x0033ec74)
    EnemyDrawCounter* counters;         // +0x30: `str r0,[sb,#0x30]` (0x0033eca8)
    u32 max_counter_8;                  // +0x34: `str r0,[sb,#0x34]` (0x0033f370)
    u32 max_counter_6;                  // +0x38: `str r0,[sb,#0x38]` (0x0033f358)
};
static_assert(offsetof(EnemyDrawWork, header) == 0x10);
static_assert(offsetof(EnemyDrawWork, models) == 0x14);
static_assert(offsetof(EnemyDrawWork, units) == 0x18);
static_assert(offsetof(EnemyDrawWork, index_array) == 0x1C);
static_assert(offsetof(EnemyDrawWork, entries) == 0x20);
static_assert(offsetof(EnemyDrawWork, records) == 0x2C);
static_assert(offsetof(EnemyDrawWork, counters) == 0x30);
static_assert(offsetof(EnemyDrawWork, max_counter_8) == 0x34);
static_assert(offsetof(EnemyDrawWork, max_counter_6) == 0x38);

/**
 * Global at 0x00433D98 read through `fp` by EnemyDraw_func_0033eadc
 * (`vldr s23,[fp,#0x10]`, 0x0033eb00).
 */
struct EnemyDrawGlobal {
    u8  pad_00[4];
    f32 field_04;                       // +0x04: `vldr s1,[fp,#4]` (0x0033f0d4)
    u8  pad_08[4];
    f32 field_0C;                       // +0x0C: `vldrne s0,[fp,#0xc]` (0x0033f1ec)
    f32 field_10;                       // +0x10: `vldr s23,[fp,#0x10]` (0x0033eb00)
};
static_assert(offsetof(EnemyDrawGlobal, field_04) == 0x04);
static_assert(offsetof(EnemyDrawGlobal, field_0C) == 0x0C);
static_assert(offsetof(EnemyDrawGlobal, field_10) == 0x10);

extern EnemyDrawGlobal g_EnemyDrawGlobal;   // 0x00433D98

void EnemyDraw_func_0033eadc(EnemyDrawWork* work);

// ---------------------------------------------------------------------------
// EftLoadFile.c (0x00249FAC)
//
// Original Atlus source path:
//   c:\SMT4\XRD686\sdds4\program\battle\Effect\EftLoadFile.c
// ---------------------------------------------------------------------------

/** Header reached by `r8 = path + 8` (0x0024A04C). */
struct EftFileHeader {
    u32 pad_00;
    u32 item_count;                     // +0x04 of header (= path+0x0C): `ldr r0,[r8,#4]`
    u32 effect_count;                   // +0x08 of header (= path+0x10): `ldr r0,[r8,#8]`
    u8  pad_0C[0x90];                   // +0x0C..+0x9C
};
static_assert(offsetof(EftFileHeader, item_count) == 0x04);
static_assert(offsetof(EftFileHeader, effect_count) == 0x08);

/**
 * One 0x348-byte destination effect record.
 *
 * The source stride is 0x228 for pre-v4 files (0x0024A0F0 loop) and 0x348
 * for v4+ files (0x0024A06C `mul r2,r0,#0x348`).
 */
struct EftRecord {
    f32 transform[8];                   // +0x000..+0x020: `vldmia r5`/`vstmia r4`
    u8  pad_020[0x134];                 // +0x020..+0x154: copy of source +0x20
    u8  pad_154[0xB0];                  // +0x154..+0x204: copy of source +0x154
    f32 anim[8];                        // +0x204..+0x224: `vldmia`/`vstmia` at 0x0024A140
    u32 field_224;                      // +0x224 = 0 (0x0024A14C)
    u32 field_228;                      // +0x228 = callback result (0x0024A480)
    u8  pad_22C[0x118];                 // +0x22C..+0x344
    u8  flag_344;                       // +0x344: copied from source +0x224 (0x0024A130)
    u8  pad_345[3];                     // +0x345..+0x348
};
static_assert(offsetof(EftRecord, anim) == 0x204);
static_assert(offsetof(EftRecord, field_228) == 0x228);
static_assert(offsetof(EftRecord, flag_344) == 0x344);
static_assert(sizeof(EftRecord) == 0x348);

/** One 20-byte item descriptor allocated at 0x0024A4C8. */
struct EftItem {
    u32 field_00;
    u32 field_04;
    s32 offset_x;                       // +0x08: `vldr s0,[r0,#8]` (0x0024A738)
    s32 offset_y;                       // +0x0C: `vldr s0,[r0,#0xc]` (0x0024A748)
    s32 offset_z;                       // +0x10: `vldr s0,[r0,#0x10]` (0x0024A758)
};
static_assert(offsetof(EftItem, offset_x) == 0x08);
static_assert(sizeof(EftItem) == 0x14);

s32 EftLoadFile_func_00249fac(s32 effect_id, const u8* path);

// ---------------------------------------------------------------------------
// titleDbgBg.cpp (0x00117CA4)
//
// Original Atlus source path:
//   c:\SMT4\XRD686\sdds4\program\title\titleDbgBg.cpp
// ---------------------------------------------------------------------------

/**
 * Title debug-background scene.  The listing reaches +0x13DC through r5
 * (`add r5,r5,#0x3dc` after `add r5,r0,#0xc00`, 0x00117CC0/0x00117CC8), so
 * this reconstruction keeps a scene-local type rather than reusing the
 * 0xFEC-byte FrameTexScene from engine/asd_frame.h.
 */
struct TitleDbgBgWork {
    u8  pad_0000[0xEE4];
    u8  field_ee4;                      // +0x0EE4: `ldrb r0,[r4,#0xee4]` (0x00117D90)
    u8  pad_ee5[3];
    f32 field_ee8;                      // +0x0EE8: `vldr s0,[ip,#0x2e8]` (0x00117F9C)
    f32 field_eec;                      // +0x0EEC: `vldr s3,[ip,#0x2ec]` (0x00117F94)
    f32 field_ef0;                      // +0x0EF0: `vldr s6,[ip,#0x2f0]` (0x00117F8C)
    f32 field_ef4;                      // +0x0EF4: `vldr s9,[ip,#0x2f4]` (0x00117F84)
    f32 field_ef8;                      // +0x0EF8: `vldr s1,[ip,#0x2f8]` (0x00117F98)
    f32 field_efc;                      // +0x0EFC: `vldr s4,[ip,#0x2fc]` (0x00117F90)
    f32 field_f00;                      // +0x0F00: `vldr s7,[ip,#0x300]` (0x00117F88)
    f32 field_f04;                      // +0x0F04: `vldr s10,[ip,#0x304]` (0x00117F80)
    u8  pad_f08[8];
    void* field_f10;                    // +0x0F10: `ldr r3,[r4,#0xf10]` (0x00117F5C)
    f32 field_f14;                      // +0x0F14: `vldr s2,[ip,#0x314]` (0x00117F60)
    s32 field_f18;                      // +0x0F18: `ldr r0,[r4,#0xf18]` (0x00117E50)
    u8  field_f1c;                      // +0x0F1C: `ldrb r0,[r4,#0xf1c]` (0x00117DC4)
    u8  pad_f1d[3];
    engine::AsdTexture* overlay_textures[2]; // +0x0F20/+0x0F24
    u8  pad_f28[0xB4];
    engine::AsdTexture* field_fdc;      // +0x0FDC: `ldr r6,[r4,#0xfdc]` (0x00117D94)
    u8  pad_fe0[0x3FC];                 // +0x0FE0..+0x13DC
    engine::AsdTexture* field_13dc;     // +0x13DC: `ldr r2,[r5]` (0x00117CF8)
};
static_assert(offsetof(TitleDbgBgWork, field_ee4) == 0xEE4);
static_assert(offsetof(TitleDbgBgWork, field_ee8) == 0xEE8);
static_assert(offsetof(TitleDbgBgWork, field_f10) == 0xF10);
static_assert(offsetof(TitleDbgBgWork, field_f18) == 0xF18);
static_assert(offsetof(TitleDbgBgWork, field_f1c) == 0xF1C);
static_assert(offsetof(TitleDbgBgWork, overlay_textures) == 0xF20);
static_assert(offsetof(TitleDbgBgWork, field_fdc) == 0xFDC);
static_assert(offsetof(TitleDbgBgWork, field_13dc) == 0x13DC);

extern TitleDbgBgWork* g_TitleDbgBgWork;     // 0x0043E278

void titleDbgBg_func_00117ca4(s32 mode);

// ---------------------------------------------------------------------------
// FilterXPoly.cpp (0x00348548)
//
// Original Atlus source path:
//   c:\SMT4\XRD686\sdds4\program\battle\Filter\FilterXPoly.cpp
// ---------------------------------------------------------------------------

/** Input descriptor read through `self->+0x60`. */
struct FilterXData {
    s32 count;                          // +0x00: `ldr r0,[r0]` (0x003485B4)
    f32 field_04;                       // +0x04: `vldr s2,[r0,#4]` (0x00348718)
    u8  pad_08[8];
    f32 uv0[2];                         // +0x10: `vldmia r1,{s12,s13}` (0x00348764)
    f32 field_18;                       // +0x18: `vldr s12,[r1,#0x18]` (0x00348788)
    u32 field_1C;                       // +0x1C: `ldr r1,[r1,#0x1c]` (0x0034878C)
    f32 uv1[2];                         // +0x20: `add r3,r3,#0x20` (0x00348830)
    u8  pad_28[4];
    s32 field_2C;                       // +0x2C: `ldr r2,[r1,#0x2c]` (0x00348560)
};
static_assert(offsetof(FilterXData, count) == 0x00);
static_assert(offsetof(FilterXData, uv0) == 0x10);
static_assert(offsetof(FilterXData, field_18) == 0x18);
static_assert(offsetof(FilterXData, uv1) == 0x20);
static_assert(offsetof(FilterXData, field_2C) == 0x2C);

/** One 0x14-byte vertex produced by FilterXPoly_func_00348548. */
struct FilterXVertex {
    f32 x;                              // +0x00: `vstmia r3!,{s2}` (0x00348800)
    f32 y;                              // +0x04: `vstmia r3,{s0,s1}` (0x00348808)
    f32 z;                              // +0x08
    f32 u;                              // +0x0C: `vstmia r1,{s12,s13}` (0x00348828)
    f32 v;                              // +0x10
};
static_assert(sizeof(FilterXVertex) == 0x14);

/** Filter workspace (allocation sizes in the listing: (count+1)*0x14). */
struct FilterXPolyWork {
    u32 field_00;
    FilterXVertex* vertices;            // +0x04: `str r0,[r4,#4]` (0x003485A8)
    u8  pad_08[0x10];
    u8  field_18[0x40];                 // +0x18: passed to 0x002C0000 (0x003488DC)
    f32 field_58;                       // +0x58: `vstmia r1,{s16,s17}` (0x00348868)
    f32 field_5C;                       // +0x5C
    FilterXData* data;                  // +0x60: `str r1,[r4,#0x60]` (0x0034855C)
    u16* indices;                       // +0x64: `str r0,[r4,#0x64]` (0x003485C8)
};
static_assert(offsetof(FilterXPolyWork, vertices) == 0x04);
static_assert(offsetof(FilterXPolyWork, field_18) == 0x18);
static_assert(offsetof(FilterXPolyWork, field_58) == 0x58);
static_assert(offsetof(FilterXPolyWork, data) == 0x60);
static_assert(offsetof(FilterXPolyWork, indices) == 0x64);

/** One 16-byte row of the .rodata angle table at 0x00407FC0. */
struct FilterTrigRow {
    f32 x;
    f32 y;
    f32 z;
    f32 w;
};
static_assert(sizeof(FilterTrigRow) == 0x10);

void FilterXPoly_func_00348548(FilterXPolyWork* self, void* source, s32 arg);

// ---------------------------------------------------------------------------
// EffectProcess.cpp (0x002217D8)
//
// Original Atlus source path:
//   c:\SMT4\XRD686\sdds4\program\battle\Effect\EffectProcess.cpp
// ---------------------------------------------------------------------------

struct EffectProcessWork {
    u8  pad_000[0x508];                 // +0x000..+0x508
    f32 field_508;                      // +0x508: `vstr s2,[r8]` (0x0022186C)
    f32 field_50C;                      // +0x50C
    f32 field_510;                      // +0x510 = 5.0 (0x0022187C)
    f32 field_514;                      // +0x514: `vstr s2,[r7]` (0x00221880)
    f32 field_518;                      // +0x518
    f32 field_51C;                      // +0x51C
    f32 field_520;                      // +0x520 = 60.0 (0x00221894)
    void* task;                         // +0x524: `str r0,[r4,#0x524]` (0x0022190C)
    void* draw_up;                      // +0x528: `str r0,[r4,#0x528]` (0x00221978)
    void* draw_down;                    // +0x52C: `str r0,[r4,#0x52c]` (0x0022194C)
    u8  mode;                           // +0x530: `strb r5,[r4,#0x530]` (0x00221828)
};
static_assert(offsetof(EffectProcessWork, field_508) == 0x508);
static_assert(offsetof(EffectProcessWork, field_520) == 0x520);
static_assert(offsetof(EffectProcessWork, task) == 0x524);
static_assert(offsetof(EffectProcessWork, draw_up) == 0x528);
static_assert(offsetof(EffectProcessWork, draw_down) == 0x52C);
static_assert(offsetof(EffectProcessWork, mode) == 0x530);

extern EffectProcessWork* g_EffectProcessWork;   // 0x00433260

void* EffectProcess_func_002217d8(u8 mode);

// ---------------------------------------------------------------------------
// btlTalkCommand.cpp (0x00318770)
//
// Original Atlus source path:
//   c:\SMT4\XRD686\sdds4\program\battle\Talk\btlTalkCommand.cpp
// ---------------------------------------------------------------------------

/** Battle/talk record returned by 0x002B087C (unit id at +0x00). */
struct BtlTalkUnitRecord {
    u16 id;                             // +0x00
    u8  field_02;                       // +0x02: `ldrb r1,[r5,#2]` (0x003187C0)
    u8  field_03;                       // +0x03: `ldrb r1,[r5,#3]` (0x003188A0)
    u8  pad_04[0x12];
    u16 flags;                          // +0x16: `ldrh r0,[r5,#0x16]` (0x003187AC)
    u8  pad_18[0x6A];
    u16 linked_id;                      // +0x82: `ldrh r4,[r0,#0x82]` (0x00318784)
};
static_assert(offsetof(BtlTalkUnitRecord, field_02) == 0x02);
static_assert(offsetof(BtlTalkUnitRecord, flags) == 0x16);
static_assert(offsetof(BtlTalkUnitRecord, linked_id) == 0x82);

s32 btlTalkCommand_func_00318770();

// ---------------------------------------------------------------------------
// btlDebug.cpp (0x001E1F4C)
//
// Original Atlus source path:
//   c:\SMT4\XRD686\sdds4\program\battle\btlDebug.cpp
// ---------------------------------------------------------------------------

struct BtlDebugWork {
    void* parent;                       // +0x00: `ldr r0,[r0]` (0x001E1F74)
    u8  pad_04[0x58];
    void* calc_task;                    // +0x5C: `str r0,[r4,#0x5c]` (0x001E1FA8)
    u8  pad_60[0x4448];
    u32 flags;                          // +0x44A8: `orr r2,r2,#1` (0x001E1F6C)
};
static_assert(offsetof(BtlDebugWork, calc_task) == 0x5C);
static_assert(offsetof(BtlDebugWork, flags) == 0x44A8);
static_assert(sizeof(BtlDebugWork) == 0x44AC);

/** Debug-menu state at 0x00434388 (`str r0,[r2,#8]`, 0x001E202C). */
struct BtlDebugState {
    u32 field_00;                       // +0x00 = 0 (0x001E2034)
    u16 field_02;                       // +0x02 = 0 (0x001E2038)
    void* arg;                          // +0x04 = init argument (0x001E2030)
    void* work;                         // +0x08 = allocated 0xE5C block (0x001E202C)
};

extern BtlDebugState g_BtlDebugState;   // 0x00434388

void btlDebug_func_001e1f4c(BtlDebugWork* work, void* arg);

// ---------------------------------------------------------------------------
// btlTalkBustUp.cpp (0x002959C4)
//
// Original Atlus source path:
//   c:\SMT4\XRD686\sdds4\program\battle\Talk\btlTalkBustUp.cpp
// ---------------------------------------------------------------------------

struct BtlTalkBustUpWork {
    u8  pad_000[0x2E4];
    void* calc_task;                    // +0x2E4: "TMD CALC" (0x00295A60)
    u32 field_2e8;                      // +0x2E8 = 0 (0x00295A44)
    u32 field_2ec;                      // +0x2EC = 0 (0x00295A48)
    u8  pad_2f0[8];
    s32 field_2f8;                      // +0x2F8 = -1 (0x00295A1C)
    f32 field_2fc;                      // +0x2FC = 1.0 (0x00295A2C)
    f32 field_300;                      // +0x300 = 1.0 (0x00295A38)
    f32 field_304;                      // +0x304 = 0.0
    u32 field_308;                      // +0x308 = 0 (0x00295A24)
};
static_assert(offsetof(BtlTalkBustUpWork, calc_task) == 0x2E4);
static_assert(offsetof(BtlTalkBustUpWork, field_2f8) == 0x2F8);
static_assert(offsetof(BtlTalkBustUpWork, field_2fc) == 0x2FC);
static_assert(offsetof(BtlTalkBustUpWork, field_308) == 0x308);
static_assert(sizeof(BtlTalkBustUpWork) == 0x30C);

extern BtlTalkBustUpWork* g_BtlTalkBustUpWork;   // 0x00434210

void btlTalkBustUp_func_002959c4();

// ---------------------------------------------------------------------------
// btlEditor.cpp (0x001F7F00)
//
// Original Atlus source path:
//   c:\SMT4\XRD686\sdds4\program\battle\btlEditor.cpp
// ---------------------------------------------------------------------------

struct BtlEditorWork {
    void* parent;                       // +0x00: `ldr r0,[r0]` (0x001F7F0C)
    u8  pad_04[0x54];
    void* calc_task;                    // +0x58: `str r0,[r4,#0x58]` (0x001F7F3C)
    u8  pad_5c[0x444C];
    u32 flags;                          // +0x44A8: `orr r2,r2,#0x80000` (0x001F8010)
};
static_assert(offsetof(BtlEditorWork, calc_task) == 0x58);
static_assert(offsetof(BtlEditorWork, flags) == 0x44A8);
static_assert(sizeof(BtlEditorWork) == 0x44AC);

/** Editor state at 0x00435CE8 (0x18 bytes). */
struct BtlEditorState {
    u32 field_00;                       // +0x00 = 0 (0x001F7FA0)
    u32 field_04;                       // +0x04 = byte loaded at 0x001F7FA4
    u8  pad_08[8];
    u16 field_10;                       // +0x10 = -1 (0x001F7FB0)
    u8  field_12;                       // +0x12 = -1 (0x001F7FB4)
    u8  field_13;                       // +0x13 = -1 (0x001F7FB8)
    u8  pad_14[4];
};
static_assert(offsetof(BtlEditorState, field_04) == 0x04);
static_assert(offsetof(BtlEditorState, field_10) == 0x10);
static_assert(offsetof(BtlEditorState, field_12) == 0x12);
static_assert(sizeof(BtlEditorState) == 0x18);

extern BtlEditorState* g_BtlEditorState;    // 0x00435CE8

void btlEditor_func_001f7f00(BtlEditorWork* work);

// ---------------------------------------------------------------------------
// btlGameOver.cpp (0x0021AE48)
//
// Original Atlus source path:
//   c:\SMT4\XRD686\sdds4\program\battle\btlGameOver.cpp
// ---------------------------------------------------------------------------

struct BtlGameOverWork {
    void* parent;                       // +0x00: `ldr r0,[r0]` (0x0021AE54)
    u8  pad_04[0x28];
    void* calc_task;                    // +0x2C: `str r0,[r4,#0x2c]` (0x0021AE84)
    u8  pad_30[0x4470];
    u32 flags;                          // +0x44A0: `orr r2,r2,#0x80000000` (0x0021AF50)
};
static_assert(offsetof(BtlGameOverWork, calc_task) == 0x2C);
static_assert(offsetof(BtlGameOverWork, flags) == 0x44A0);
static_assert(sizeof(BtlGameOverWork) == 0x44A4);

/** Game-over state at 0x00435D60; +0x04 is ORed with 1 (0x0021AF48). */
struct BtlGameOverState {
    u32 field_00;
    u32 field_04;                       // +0x04: `str r0,[r5,#4]` (0x0021AF48)
    u8  pad_08[0x38];
};
static_assert(offsetof(BtlGameOverState, field_04) == 0x04);
static_assert(sizeof(BtlGameOverState) == 0x40);

extern BtlGameOverState* g_BtlGameOverState;    // 0x00435D60

void btlGameOver_func_0021ae48(BtlGameOverWork* work);

} // namespace smt4::battle
