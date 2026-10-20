#include "engine/map_runtime.h"
#include "engine/asd_symbols.h"
#include "engine/asd_effect.h"
#include "camp/unite.h"
#include <cstdint>

namespace smt4::engine {

// ---------------------------------------------------------------------------
// Globals (addresses are the storage locations used by the listing)
// ---------------------------------------------------------------------------

LmapMainWork* g_LmapMainWork = nullptr;                 // 0x00447060 (BSS)
MapSceneView* g_MapSceneView = nullptr;                 // 0x00447E88 (BSS slot)
MapIfWork* g_MapIfWork = nullptr;                       // 0x00447A78 (BSS)
MapEnemyWork* g_MapEnemyWork = nullptr;                 // 0x00447600 (BSS)
MapDepartWork* g_MapDepartWork = nullptr;               // 0x004475B8 (BSS)
MapEplWork* g_MapEplWork = nullptr;                     // 0x00447A10 (BSS)
MapMainWork* g_MapMainWork = nullptr;                   // 0x00447E28 (BSS)
EventOpeningWork* g_EventOpeningWork = nullptr;         // 0x0043DF98 (.data, 0)
NaviMainWork* g_NaviMainWork = nullptr;                 // 0x0044CDF0 (BSS)

// 0x004B5D30 (BSS): three 0x30-byte projection quads at +0x000/+0x630/+0xC60.
MapIfProjectionTables g_MapIfProjectionTables{};

// 0x0049F91C (BSS): shared map/script word block (see map_runtime.h).
u8 g_MapRuntimeState[0x22C] = {};

// ---------------------------------------------------------------------------
// Observed call targets (addresses are the branch targets in code.bin)
// ---------------------------------------------------------------------------

extern "C" {
    // AsdMemory (c:\SMT4\XRD686\AsdSDK\Source\Sys\Mem\AsdMemory.cpp)
    void* AsdMem_Alloc(u32 a0, u32 a1, u32 a2, u32 size, u32 flag);        // 0x002C4B84
    void* AsdMem_AllocAlign(u32 a0, u32 a1, u32 a2, u32 size, u32 flag);   // 0x002C54F0
    void  AsdMem_Zero(void* ptr, u32 size);                                // 0x002C4B30
    void  AsdMem_Free(void* ptr);                                          // 0x002C4360

    // 0x002C2B1C: engine context singleton (same spelling as src/ui/window.cpp).
    void* UiEngine_GetContext();

    // 0x00280D30: FrameTex pair selection, `mov r0,#1` at every map call site.
    void  FrameTex_func_00280d30(u32 alternate);

    // AsdCamera.cpp helpers (canonical spellings from src/engine/asd_scene.cpp).
    void  AsdCamera_InitProjection(void* projection, u32 mode);            // 0x002C2210
    void  AsdCamera_LookAt(void* projection, const f32* eye,
                           const f32* target, const f32* up);              // 0x002C20A8
    void  AsdCamera_SetPerspective(void* projection, u32 mode, f32 p0,
                                   f32 p1, f32 p2, f32 p3);                // 0x002C1FFC
    s32   AsdScene_LoadMode();                                             // 0x002C1F28

    // 0x002C1774 (16 B): `add r0,r0,#0x400` then `vstr s0,[r0,#0x104]` /
    // `vstr s1,[r0,#0x100]`, i.e. it stores the two incoming floats at
    // projection +0x504 / +0x500.
    void  AsdCamera_SetClipRange(void* projection, f32 s0, f32 s1);

    // 0x00298FEC (20 B): stores r0 into the camera's first projection slot
    // (`ldr r1,[0x0044ea58]; ldr r1,[r1,#4]; str r0,[r1,#0x80]`).
    void  AsdCamera_BindProjection(void* projection);

    // 0x00396534 (88 B): clears a 0xA8-byte map panel block (words at +0x00,
    // +0x0C..+0x14, the 0x20-word run at +0x18, +0x98/+0x9C and +0xA0).
    void  engine_func_00396534(void* block);

    // Map sub-manager resets reached from mapMain (0x001B44C0..0x001B44D8).
    void  mapEpl_func_00192298();                                          // 0x00192298
    void  engine_func_001b4664();                                          // 0x001B4664
    void  engine_func_001b3ca0();                                          // 0x001B3CA0
    void  engine_func_00192320();                                          // 0x00192320
    void  engine_func_0018ab7c();                                          // 0x0018AB7C
    void  engine_func_001923d0();                                          // 0x001923D0
    void  engine_func_001a8b64();                                          // 0x001A8B64

    // 0x0025C374 (252 B): resets the work words at +0x18..+0x44 and, when the
    // second argument is non-zero, copies the eight camera fields from
    // 0x0049F91C into the work block.
    void  engine_func_0025c374(void* work, u32 mode);

    // 0x00297C9C (404 B): builds the 0x80 map-interface records.  The routine
    // reloads r0 from 0x00447A78 immediately, so its argument is dead.
    void  script_vm_func_00297c9c(void* unused);

    // 0x002FB3B8 (56 B): TBB table 0x2D / sub-table 3 row count plus the
    // bundle-resident extra count; 0x002C9BA4 (120 B) returns one 0x18-byte row.
    s32   engine_func_002fb3b8();
    void* engine_func_002c9ba4(u32 index);

    // 0x002B9364 (140 B): 0x94-byte table row lookup by u16 id.  The battle and
    // UI TUs spell the same address Battle_GetTalkEntry / Item_GetTableEntry;
    // the demon-growth path reads the same byte +3 flags.
    void* Battle_GetTalkEntry(u32 id);

    // 0x0029EC14 (88 B): 4-byte table row lookup by u16 id.
    void* camp_func_0029ec14(u32 id);

    // 0x002C0BCC (56 B): LCG draw, uniformly distributed over [0, range].
    u32   Random_Range(u32 range);

    // 0x002B7F0A: qsort(base, count, size, compar); the 0x0032B570 comparator
    // lives inside func_0032b4ac and returns `b[0] - a[0]` for u16 elements.
    void  qsort_arm(void* base, s32 nmemb, u32 size,
                    s32 (*compar)(const void*, const void*));
    s32   func_0032b570(const void* a, const void* b);

    // 0x002BE7FC: sprintf-style formatter (same spelling as the other TUs).
    void  UiText_Format(char* dst, const char* fmt, ...);

    // 0x002C5E3C: build "rom:/%s", open it, read `user` bytes and return the
    // data pointer while `out_size` receives the stream size.
    void* AsdFile_LoadSync(const char* name, u32* out_size, u32 flags,
                           u32 user);

    // 0x002A3D50: apply a 4-float position/rotation block to a part container.
    void  AsdPart_Setup2(void* part, void* arg);

    // 3dEventOpening.cpp resources.
    void  engine_func_002a0c54(const char* path, u32 index);               // 0x002A0C54
    void* engine_func_00263e48(const char* path);                          // 0x00263E48
    void* engine_func_0029a2d0(const char* path, u32 size);                // 0x0029A2D0

    // naviMain.cpp helpers.
    void* engine_func_00399594(void* panel);                               // 0x00399594
    void  engine_func_003c2c58(void* fade, u8 mode);                       // 0x003C2C58
    // 0x003C2C20: fade-start entry inside ui_func_003c2b10; stores the target
    // mode byte at +8, the duration at +0xA and enters state 2 at +4.
    void  engine_func_003c2c20(void* fade, u8 duration, u8 mode);
    void  engine_func_00240e1c(u32 mode);                                  // 0x00240E1C
    void  CommonBg_func_00289b4c();                                        // 0x00289B4C
    void  ScriptVm_func_00289ae8();                                        // 0x00289AE8

    // NkmGrowEvent.cpp script notifications.
    void  script_vm_func_0029c950(void* work);                             // 0x0029C950
    void  script_vm_func_00295760(void* work);                             // 0x00295760
}

static inline void (*TaskCallback(u32 address))(void*) {
    return reinterpret_cast<void (*)(void*)>(
        static_cast<std::uintptr_t>(address));
}

static inline u32 TaskUserData(const void* pointer) {
    return static_cast<u32>(reinterpret_cast<std::uintptr_t>(pointer));
}

// ---------------------------------------------------------------------------
// lmapMain.cpp (0x001D2B14), 760 B
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x001d2b14, 760)
void lmapMain_func_001d2b14() {
    // 0x001D2B1C..0x001D2B40: the ADR source path, line 0x222 and size 0x4F04
    // are the dead debug arguments of the allocation macro.
    LmapMainWork* const work = static_cast<LmapMainWork*>(
        AsdMem_Alloc(0x100, 0x100, 0, 0x4F04, 1));
    g_LmapMainWork = work;                              // 0x001D2B4C

    u8* const engine = static_cast<u8*>(UiEngine_GetContext()); // 0x001D2B50
    FrameTex_func_00280d30(1);                          // 0x001D2B5C

    work->field_009 = 0;                                // 0x001D2B64
    work->field_00a = 0;                                // 0x001D2B68
    work->field_00b = 0;                                // 0x001D2B6C
    work->field_00c = 0;                                // 0x001D2B70
    work->field_010 = 0;                                // 0x001D2B74

    // 0x001D2B78..0x001D2B94: the three-word group at work+0xCC is only cleared
    // when its first word is non-zero.
    if (work->field_0cc != 0) {
        work->field_0cc = 0;
        work->field_0d0 = 0;
        work->field_0d4 = 0;
    }

    work->field_0c8 = 1.0f;                             // 0x001D2BA0
    work->field_0c4 = 1.0f;                             // 0x001D2BA4
    work->field_040 = 0x65;                             // 0x001D2BAC
    work->field_04c = 0;                                // 0x001D2BB0
    work->field_04e = 0;                                // 0x001D2BB4
    work->field_048 = 1;                                // 0x001D2BB8

    // 0x001D2BC0..0x001D2C04: nine floats at +0x1C and two ranges at +0x4C,
    // plus the pair at +0x15C.  s0/s1/s2 are -554.0f/0.01f/-4780.0f.
    g_MapSceneView->field_01c = -554.0f;                // 0x001D2BD4
    g_MapSceneView->field_020 = 0.01f;
    g_MapSceneView->field_024 = -4780.0f;
    g_MapSceneView->field_028 = -554.0f;                // 0x001D2BE4
    g_MapSceneView->field_02c = 0.01f;                  // 0x001D2BEC
    g_MapSceneView->field_030 = -4780.0f;
    g_MapSceneView->field_034 = -554.0f;
    g_MapSceneView->field_038 = 0.01f;                  // 0x001D2C00
    g_MapSceneView->field_03c = -4780.0f;
    g_MapSceneView->field_04c = 180.0f;                 // 0x001D2BF4
    g_MapSceneView->field_050 = 180.0f;                 // 0x001D2BF8
    g_MapSceneView->field_15c = 1000.0f;                // 0x001D2C04
    g_MapSceneView->field_160 = 3000.0f;

    // 0x001D2C08..0x001D2C10: the panel block at +0xEC is reset, then the
    // +0x994 word is cleared before the call.
    work->field_994 = 0;                                // 0x001D2C0C
    engine_func_00396534(work->block_0ec);

    work->field_0dc = 0.0f;                             // 0x001D2C1C
    work->field_0e0 = 0;                                // 0x001D2C24
    work->field_a00 = 0.0f;                             // 0x001D2C28
    work->field_a04 = 0.0f;                             // 0x001D2C2C
    work->field_a08 = 0.0f;                             // 0x001D2C30
    work->field_4eac = 0;                               // 0x001D2C48
    work->field_4eb0 = 100.0f;                          // 0x001D2C4C
    work->field_4eb4 = 20000.0f;
    work->field_4eb8 = 10.0f;

    work->field_9a4 = 0;                                // 0x001D2C54
    work->field_9a8 = 0;                                // 0x001D2C58
    work->field_9ac = 0;                                // 0x001D2C5C
    work->field_9b0 = 0;                                // 0x001D2C60
    work->field_9b4 = 0;                                // 0x001D2C64
    work->field_9b8 = 0;                                // 0x001D2C68
    work->field_9e4 = 0;                                // 0x001D2C6C
    work->field_9e8 = 0;                                // 0x001D2C70
    work->field_9ec = 0;                                // 0x001D2C74
    work->field_9f0 = 0;                                // 0x001D2C78
    work->field_a0c = 0;                                // 0x001D2C7C
    work->field_a94 = 0;                                // 0x001D2C80
    work->field_a98 = 0;                                // 0x001D2C84
    work->field_a9c = 0;                                // 0x001D2C88
    work->field_a90 = 0;                                // 0x001D2C90

    // 0x001D2C94..0x001D2CB4: the paired stores clear 0x20 words at +0xA10.
    for (s32 i = 0; i < 0x20; ++i) {
        work->field_a10[i] = 0;
    }

    // 0x001D2CBC..0x001D2CD8: 0x80 records of a 0x88-byte stride
    // (`add r3,r0,r0,lsl #4` then `lsl #3`); both leading flag bytes are
    // cleared.  The record boundary itself is not observable, so the sweep is
    // expressed over the byte extent it proves.
    for (s32 i = 0; i < 0x80; ++i) {
        work->actor_flags[i * 0x88] = 0;
        work->actor_flags[i * 0x88 + 1] = 0;
    }

    work->field_990 = 0;                                // 0x001D2CE0
    work->field_9a0 = 0;                                // 0x001D2CE4
    work->field_4f00 = 0;                               // 0x001D2CE8
    work->field_0e1 = 0;                                // 0x001D2CF4
    work->field_0e4 = 0x38;                             // 0x001D2CF8
    work->field_0e8 = 40.0f;                            // 0x001D2CFC

    engine_func_001b3ca0();                             // 0x001D2D00

    g_MapRuntimeState[0x22B] = 0;                       // 0x001D2D14
    engine[0x790] = 0;                                  // 0x001D2D08
    work->field_008 = 0;                                // 0x001D2D1C

    // 0x001D2D20..0x001D2D38: "LMAP C" carries the FlowScript opcode entry
    // (0x001D3D40) plus user words 0x0021EDD4 / 0.
    work->calc_task = AsdTask_CreateCalc(
        "LMAP C", 2, 0, 0, TaskCallback(0x001D3D40), 0x0021EDD4, 0);

    // 0x001D2D3C..0x001D2D64: "LMAP U" draw task (0x001FD950) under the calc
    // task, user word 0x002D4FDC.
    work->draw_task = AsdTask_CreateDraw(
        "LMAP U", 0x70, 0, 0, TaskCallback(0x001FD950), 0x002D4FDC, 0,
        work->calc_task);                               // 0x001D2D68
}

// ---------------------------------------------------------------------------
// mapIf.cpp (0x0018ABA8), 696 B
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x0018aba8, 696)
void mapIf_func_0018aba8(void* parent, u32 flag) {
    MapIfWork* const work = static_cast<MapIfWork*>(
        AsdMem_Alloc(0x100, 0x100, 0, 0xCCE8, 1));      // 0x0018ABE0
    g_MapIfWork = work;                                 // 0x0018ABF4

    work->field_014 = 0;                                // 0x0018ABF8
    work->field_016 = 0;                                // 0x0018ABFC
    work->field_018 = 0;                                // 0x0018AC00
    work->field_01c = 0;                                // 0x0018AC04
    work->field_020 = 0;                                // 0x0018AC08
    work->field_030 = 0;                                // 0x0018AC0C
    work->field_034 = 0;                                // 0x0018AC10
    work->field_038 = 0;                                // 0x0018AC14

    // 0x0018AC18..0x0018AC70: the scattered state bytes/words.  The address
    // chain `r1=r0+0xcc00`, `r2=r0+0xcbd0`, `r3=r0+0xcc0` and the `ip`/`sb`/`r8`
    // variants are all folded into the proven field offsets.
    work->field_cc0 = 0;                                // 0x0018AC30
    work->field_cbd0 = 0;                               // 0x0018AC20
    work->field_ccb8 = 0;                               // 0x0018AC28
    work->field_ccba = 0;                               // 0x0018AC2C
    work->field_cccc = 0.0f;                            // 0x0018AC3C
    work->field_ccd0 = 0.0f;                            // 0x0018AC40
    work->field_ccd4 = 0.0f;                            // 0x0018AC4C
    work->field_ccd8 = 0;                               // 0x0018AC58
    work->field_cce0 = 0;                               // 0x0018AC60
    work->field_cce4 = 0;                               // 0x0018AC70

    // 0x0018AC64..0x0018AC94: "MAPIF C" is a draw-shaped task (the listing uses
    // 0x002C4C00) whose parent is the caller's task, calc callback 0x0019F97C
    // and user word 0x001E5D5C.
    work->calc_task = AsdTask_CreateDraw(
        "MAPIF C", 2, 0, 0, TaskCallback(0x0019F97C), 0x001E5D5C, 0, parent);

    // 0x0018AC98..0x0018ACC0: "MAPIF U" (0x73) uses the 0x001E8390 callback and
    // the calc task as parent.
    work->up_task = AsdTask_CreateDraw(
        "MAPIF U", 0x73, 0, 0, TaskCallback(0x001E8390), 0, 0,
        work->calc_task);

    // 0x0018ACC4..0x0018ACEC: "MAP FADE" (0x85) reuses shopMain_DrawDown
    // (0x0021EE14) under the calc task; the handle is discarded.
    AsdTask_CreateDraw("MAP FADE", 0x85, 0, 0, TaskCallback(0x0021EE14),
                       0, 0, work->calc_task);

    // 0x0018ACF0..0x0018AD14: "MIF3DL" (0x6F) with callback 0x001E83FC.
    work->draw_task = AsdTask_CreateDraw(
        "MIF3DL", 0x6F, 0, 0, TaskCallback(0x001E83FC), 0, 0,
        work->calc_task);

    // 0x0018AD1C..0x0018ADC0: three 0x30-byte quads.  s0..s3 hold
    // -64.0f/16.0f/-16.0f/64.0f; the 0x630 stride comes from the
    // `add r1,r0,#0x630` / `add r2,r1,#0x630` chain.
    MapIfProjectionTables* const tables = &g_MapIfProjectionTables;

    tables->area.corner[0][0] = -64.0f;                 // 0x0018AD38
    tables->area.corner[0][1] = 16.0f;
    tables->area.corner[0][2] = 0.0f;                   // 0x0018AD2C
    tables->area.corner[1][0] = -64.0f;                 // 0x0018AD40
    tables->area.corner[1][1] = -16.0f;                 // 0x0018AD44
    tables->area.corner[1][2] = 0.0f;                   // 0x0018AD48
    tables->area.corner[2][0] = 64.0f;                  // 0x0018AD4C
    tables->area.corner[2][1] = 16.0f;                  // 0x0018AD50
    tables->area.corner[2][2] = 0.0f;                   // 0x0018AD54
    tables->area.corner[3][0] = 64.0f;                  // 0x0018AD58
    tables->area.corner[3][1] = -16.0f;                 // 0x0018AD5C
    tables->area.corner[3][2] = 0.0f;                   // 0x0018AD60

    tables->field.corner[0][0] = -64.0f;                // 0x0018AD64
    tables->field.corner[0][1] = 0.0f;                  // 0x0018AD68
    tables->field.corner[0][2] = 16.0f;                 // 0x0018AD6C
    tables->field.corner[1][0] = -64.0f;                // 0x0018AD70
    tables->field.corner[1][1] = 0.0f;                  // 0x0018AD74
    tables->field.corner[1][2] = -16.0f;                // 0x0018AD84
    tables->field.corner[2][0] = 64.0f;                 // 0x0018AD84 (vstmia)
    tables->field.corner[2][1] = 0.0f;                  // 0x0018AD78
    tables->field.corner[2][2] = 16.0f;                 // 0x0018AD7C
    tables->field.corner[3][0] = 64.0f;                 // 0x0018AD8C
    tables->field.corner[3][1] = 0.0f;                  // 0x0018AD90
    tables->field.corner[3][2] = -16.0f;                // 0x0018AD94

    tables->opening.corner[0][0] = -64.0f;              // 0x0018AD98
    tables->opening.corner[0][1] = 0.0f;                // 0x0018AD9C
    tables->opening.corner[0][2] = -16.0f;              // 0x0018ADA0
    tables->opening.corner[1][0] = -64.0f;              // 0x0018ADA4
    tables->opening.corner[1][1] = 0.0f;                // 0x0018ADA8
    tables->opening.corner[1][2] = 16.0f;               // 0x0018ADAC
    tables->opening.corner[2][0] = 64.0f;               // 0x0018ADB0
    tables->opening.corner[2][1] = 0.0f;                // 0x0018ADB4
    tables->opening.corner[2][2] = -16.0f;              // 0x0018ADC0 (vstmia)
    tables->opening.corner[3][0] = 64.0f;               // 0x0018ADC0 (vstmia)
    tables->opening.corner[3][1] = 0.0f;                // 0x0018ADB8
    tables->opening.corner[3][2] = 16.0f;               // 0x0018ADBC

    work->field_015 = static_cast<u8>(flag);            // 0x0018ADC4

    // 0x0018ADD4: tail call into the map-interface record builder.  The
    // listing leaves r0 = tables + 0xC80 (the opening quad's corner[2][2]), a
    // value the callee reloads away from 0x00447A78 before using it.
    script_vm_func_00297c9c(&tables->opening.corner[2][2]);
}

// ---------------------------------------------------------------------------
// NkmGrowEvent.cpp (0x0033BB94), 564 B
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x0033bb94, 564)
u16 NkmGrowEvent_func_0033bb94(NkmGrowEventWork* work) {
    // 0x0033BBC4: aligned 0x3EA-byte candidate list (0x1F4 ids * 2 bytes plus
    // the two-byte tail).
    u16* const candidates = static_cast<u16*>(
        AsdMem_AllocAlign(0x100, 0x100, 0, 0x3EA, 1));

    // 0x0033BBCC..0x0033BBD4: species id -> 0x94-byte growth row.
    const NkmGrowEntry* const entry = static_cast<const NkmGrowEntry*>(
        Battle_GetTalkEntry(work->species));

    // 0x0033BBE0..0x0033BC0C: highest rank (bits 0x1F of byte +3) over the
    // eight non-zero party member ids.
    s32 rank = 0;
    for (s32 i = 0; i < 8; ++i) {
        const u16 id = entry->members[i];
        if (id == 0) {
            continue;
        }
        const NkmGrowState* const state = static_cast<const NkmGrowState*>(
            camp_func_0029ec14(id));
        const s32 value = static_cast<s32>(state->field_03 & 0x1F);
        if (value > rank) {
            rank = value;
        }
    }

    // 0x0033BC10..0x0033BC28: a 3% roll promotes the rank by one.
    if (Random_Range(0x63) < 3) {
        ++rank;
    }

    // 0x0033BC1C..0x0033BC80: the 16-entry scan list is the work's eight owned
    // ids copied as one 16-byte block, followed by the eight row levels.
    u16 slots[16];
    for (s32 i = 0; i < 8; ++i) {
        slots[i] = work->owned[i];
    }
    for (s32 i = 0; i < 8; ++i) {
        slots[8 + i] = entry->levels[i].value;
    }
    qsort_arm(slots, 0x10, 2,
              reinterpret_cast<s32 (*)(const void*, const void*)>(
                  &func_0032b570));

    // 0x0033BC88..0x0033BD00: collect every id <= 0x1F4 whose byte +3 has bit
    // 0x80 set and whose rank equals the current rank, skipping ids the sorted
    // list already contains.  When nothing matches, the rank is decremented
    // and the sweep repeats down to 0.
    s32 count;
    do {
        count = 0;
        for (u32 id = 1; id <= 0x1F4; ++id) {
            const NkmGrowState* const state =
                static_cast<const NkmGrowState*>(camp_func_0029ec14(id));
            if ((state->field_03 & 0x80) == 0) {
                continue;
            }
            if (static_cast<s32>(state->field_03 & 0x1F) != rank) {
                continue;
            }

            // 0x0033BCB4..0x0033BCD4: scan from slot 0 for this id or for a
            // free slot; a completely full list still accepts the id
            // (0x0033BCD8).
            s32 slot = 0;
            while (slot < 0x10) {
                if (slots[slot] == static_cast<u16>(id)) {
                    break;
                }
                if (slots[slot] == 0) {
                    break;
                }
                ++slot;
            }
            if (slot < 0x10 && slots[slot] == static_cast<u16>(id)) {
                continue;
            }
            candidates[count] = static_cast<u16>(id);
            ++count;
        }
        if (count > 0) {
            break;
        }
        --rank;
    } while (rank >= 0);

    // 0x0033BD04..0x0033BD3C: pick one candidate and put it in the first empty
    // owned slot.  When all eight slots are taken the result stays 0.
    u16 chosen = 0;
    if (count > 0) {
        const u32 pick = Random_Range(static_cast<u32>(count - 1));
        for (s32 i = 0; i < 8; ++i) {
            if (work->owned[i] != 0) {
                continue;
            }
            chosen = candidates[pick];
            work->owned[i] = chosen;
            break;
        }
    }

    script_vm_func_0029c950(work);                      // 0x0033BD44
    script_vm_func_00295760(work);                      // 0x0033BD50
    AsdMem_Free(candidates);                            // 0x0033BD5C
    return chosen;
}

// ---------------------------------------------------------------------------
// mapEnemy.cpp (0x001A8924), 552 B
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x001a8924, 552)
void mapEnemy_func_001a8924(void* parent) {
    MapEnemyWork* const work = static_cast<MapEnemyWork*>(
        AsdMem_Alloc(0x100, 0x100, 0, 0x30F4, 1));      // 0x001A8958
    g_MapEnemyWork = work;                              // 0x001A896C

    // 0x001A8960..0x001A8994: "MENEMY" is a draw-shaped task with callback
    // 0x001D9198 and the delete helper 0x0021EDEC as its first user word.
    work->task = AsdTask_CreateDraw(
        "MENEMY", 2, 0, 0, TaskCallback(0x001D9198), 0x0021EDEC, 0, parent);

    work->field_004 = 0;                                // 0x001A899C
    work->field_008 = 0;                                // 0x001A89A0
    work->field_00c = 0;                                // 0x001A89A8
    work->field_010 = 0;                                // 0x001A89AC
    work->field_3034 = 0;                               // 0x001A89B0
    work->field_3038 = 0;                               // 0x001A89B4
    work->field_303c = 0;                               // 0x001A89B8
    work->field_3040 = 0;                               // 0x001A89BC
    work->field_3048 = 0;                               // 0x001A89CC
    work->field_3049 = 0;                               // 0x001A89D8

    // 0x001A89DC..0x001A8AC4: 0x20 records of 0x180 bytes.  s16 is 0.0f, s17
    // is 99999.0f, r8 is -1, sb is 1 and sl is 999.
    for (s32 i = 0; i < 0x20; ++i) {
        MapEnemyEntry* const entry = &work->entries[i];
        entry->field_00 = 0;                            // `strb r7,[r4,#0x34]!`
        entry->index = static_cast<u32>(i);             // 0x001A89EC
        entry->field_08 = 0.0f;                         // 0x001A89F0
        entry->field_0c = 0.0f;                         // 0x001A89F4
        entry->field_10 = 0.0f;                         // 0x001A89F8
        entry->field_14 = entry->field_08;              // 0x001A89FC/0x001A8A04
        entry->field_18 = entry->field_0c;
        entry->field_1c = 0.0f;                         // 0x001A8A0C
        entry->field_20 = 0.0f;                         // 0x001A8A10
        entry->field_24 = 0.0f;                         // 0x001A8A14
        entry->field_28 = 0.0f;                         // 0x001A8A18
        entry->field_2c = 0.0f;                         // 0x001A8A1C
        entry->field_30 = 0;                            // 0x001A8A20
        entry->field_34 = -1;
        entry->field_38 = 1;
        entry->field_3c = 99999.0f;                     // 0x001A8A28
        entry->field_50 = 0;                            // 0x001A8A2C
        entry->field_54 = 0;                            // 0x001A8A30
        entry->field_58 = 0;                            // 0x001A8A34
        entry->field_5c = 0;                            // 0x001A8A38
        entry->field_60 = 0;                            // 0x001A8A3C
        entry->field_64 = 0;                            // 0x001A8A40
        entry->field_68 = 0;                            // 0x001A8A44
        entry->field_6c = 0;                            // 0x001A8A48
        entry->field_70 = 0;                            // 0x001A8A4C
        entry->field_74 = 0;                            // 0x001A8A50
        entry->field_78 = 1;
        entry->field_7c = 0;                            // 0x001A8A58
        entry->field_7d = 0;                            // 0x001A8A5C
        entry->field_7e = 0;                            // 0x001A8A60
        entry->field_84 = 0;                            // 0x001A8A64
        entry->field_88 = 0;                            // 0x001A8A68
        entry->field_8c = Random_Range(0x64) + 0x1E;    // 0x001A8A6C..0x001A8A7C
        entry->field_90 = 0;
        entry->field_16c = 0;                           // 0x001A8A84
        entry->field_13c = 0;                           // 0x001A8A88
        entry->field_13d = 0;                           // 0x001A8A8C
        entry->field_138 = 0;                           // 0x001A8A90
        entry->field_13a = 0;                           // 0x001A8A94
        entry->field_13e = 0;                           // 0x001A8A98
        entry->field_140 = 0;                           // 0x001A8A9C
        entry->field_144 = 0;                           // 0x001A8AA0
        entry->field_148 = 0.0f;                        // 0x001A8AA4
        entry->field_170 = 999;                         // 0x001A8AAC
        entry->field_174 = 0;                           // 0x001A8AA8
        entry->field_178 = 0;                           // 0x001A8AB0
        entry->field_17c = 0;                           // 0x001A8AB8
        entry->field_17d = 0;                           // 0x001A8ABC
    }

    // 0x001A8AC8..0x001A8AEC: 0x15 spawn slots at work+0x304C.
    for (s32 i = 0; i < 0x15; ++i) {
        work->spawns[i].field_00 = 0;                   // 0x001A8ADC
        work->spawns[i].field_04 = 0;                   // 0x001A8AE0
        work->spawns[i].field_05 = 0;                   // 0x001A8AE8
    }
}

// ---------------------------------------------------------------------------
// mapDepart.cpp (0x0027EE6C), 552 B
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x0027ee6c, 552)
void mapDepart_func_0027ee6c(const MapDepartRequest* request) {
    MapDepartWork* const work = static_cast<MapDepartWork*>(
        AsdMem_Alloc(0x100, 0x100, 0, 0x80, 1));        // 0x0027EE9C
    g_MapDepartWork = work;                             // 0x0027EEA8

    u8* const engine = static_cast<u8*>(UiEngine_GetContext()); // 0x0027EEAC

    if (request == nullptr) {
        // 0x0027EEB8/0x0027EF88: without a request the default mode is 1.
        engine_func_0025c374(work, 1);
    } else {
        switch (request->mode) {                        // 0x0027EEC0
            case 0:
                engine_func_0025c374(work, 1);          // 0x0027EEEC
                work->field_00c = 0;                    // 0x0027EEF0
                work->field_010 = request->field_04;    // 0x0027EEF8
                // 0x0027EEFC..0x0027EF00: the engine context caches the same
                // word at +0x24.
                *reinterpret_cast<u32*>(engine + 0x24) = request->field_04;
                break;
            case 1:
                engine_func_0025c374(work, 0);          // 0x0027EF1C
                work->field_00c = 1;                    // 0x0027EF20
                work->field_014 = request->field_08;    // 0x0027EF28
                break;
            case 2:
                engine_func_0025c374(work, 0);          // 0x0027EF44
                work->field_00c = 2;                    // 0x0027EF4C
                work->field_014 = request->field_08;    // 0x0027EF54
                break;
            default:
                break;                                  // 0x0027EEE0 -> 0x0027EF94
        }

        // 0x0027EF04..0x0027EF10 (repeated at 0x0027EF2C and 0x0027EF58): the
        // four tail words are copied only when the shared runtime word is at
        // least 100.  The default case branches straight past this block.
        if (request->mode <= 2 &&
            *reinterpret_cast<const s32*>(g_MapRuntimeState) >= 0x64) {
            work->field_048 = request->field_10;        // 0x0027EF68
            work->field_04c = request->field_14;        // 0x0027EF70
            work->field_050 = request->field_18;        // 0x0027EF78
            work->field_054 = request->field_1c;        // 0x0027EF80
        }
    }

    // 0x0027EF94..0x0027F014: "DEPART C" (0x001E5448, user word 0x002CA030)
    // plus the "SEARCH3D" (0x6F) and "SEARCH2D" (0x73) draw tasks.
    work->field_008 = 0;                                // 0x0027EF9C
    work->calc_task = AsdTask_CreateCalc(
        "DEPART C", 2, 0, 0, TaskCallback(0x001E5448), 0x002CA030, 0);

    AsdTask_CreateDraw("SEARCH3D", 0x6F, 0, 0, TaskCallback(0x002CA650),
                       0x002F4AE8, 0, work->calc_task); // 0x0027EFE8
    AsdTask_CreateDraw("SEARCH2D", 0x73, 0, 0, TaskCallback(0x002CA048),
                       0x002F4AE4, 0, work->calc_task); // 0x0027F014
}

// ---------------------------------------------------------------------------
// 3dEventOpening.cpp (0x002F62D0), 552 B
// ---------------------------------------------------------------------------
//
// The ledger spells this entry point `3dEventOpening_func_002f62d0`; a C++
// identifier cannot begin with a digit, so the exact spelling is pinned in the
// literal that follows the marker and the definition uses the legal spelling.

// DECOMP_FUNC(0x002f62d0, 552)
static constexpr char k_3dEventOpeningSymbol[] =
    "3dEventOpening_func_002f62d0(0x002F62D0, 552 B)";
void* EventOpening3d_func_002f62d0() {
    if (g_EventOpeningWork == nullptr) {                // 0x002F62D8..0x002F62E4
        EventOpeningWork* const work = static_cast<EventOpeningWork*>(
            AsdMem_Alloc(0x100, 0x100, 0, 0x574, 1));   // 0x002F6310
        g_EventOpeningWork = work;                      // 0x002F631C
        AsdMem_Zero(work, 0x574);                       // 0x002F6320

        AsdCamera_InitProjection(&work->projection, 1); // 0x002F632C

        // 0x002F6334..0x002F63A0: eye (0,0,0), target (0,0,5), up (0,1,0),
        // perspective (30,1,10000,1.6666666) and the +0x550 range word.
        work->eye[0] = 0.0f;                            // 0x002F6340
        work->eye[1] = 0.0f;                            // 0x002F6344
        work->eye[2] = 0.0f;                            // 0x002F634C
        work->target[0] = 0.0f;                         // 0x002F6354
        work->target[1] = 0.0f;                         // 0x002F6358
        work->target[2] = 5.0f;                         // 0x002F6364
        work->up[0] = 0.0f;                             // 0x002F6388
        work->up[1] = 1.0f;                             // 0x002F6390
        work->up[2] = 0.0f;                             // 0x002F6390
        work->perspective[0] = 30.0f;                   // 0x002F6370
        work->perspective[1] = 1.0f;                    // 0x002F6378
        work->perspective[2] = 10000.0f;                // 0x002F6380
        work->perspective[3] = 1.6666666f;              // 0x002F639C
        work->field_550 = 5.0f;                         // 0x002F63A0

        // 0x002F63A4..0x002F63D4: the two clip floats arrive in s0/s1.
        AsdCamera_SetClipRange(&work->projection, 5.0f, 1.0f);
        AsdCamera_LookAt(&work->projection, work->eye, work->target,
                         work->up);                     // 0x002F63B8
        AsdCamera_SetPerspective(&work->projection, 1,
                                 work->perspective[0], work->perspective[1],
                                 work->perspective[2], work->perspective[3]);
        AsdCamera_BindProjection(&work->projection);    // 0x002F63D4

        // 0x002F63D8..0x002F63FC: calc task (0x00205020, user words 0x002EFF30
        // and the work itself).
        work->calc_task = AsdTask_CreateCalc(
            "3dEventOpening Calc", 2, 0, 0, TaskCallback(0x00205020),
            0x002EFF30, TaskUserData(work));

        // 0x002F6404..0x002F6420: the scene load mode is queried and discarded
        // (the `cmp r0,#0` at 0x002F640C does not guard the store); the pair at
        // +0x564 is then set to 1/0.
        (void)AsdScene_LoadMode();
        work->field_564 = 1;
        work->field_568 = 0;

        // 0x002F6424..0x002F6458: loop environment, both camera tracks, the
        // loop model (0x38) and the +0x570 start word.
        engine_func_002a0c54("event/oc/oc_loop.bcenv", 0);
        work->field_558 = 0;
        work->cam_loop = engine_func_00263e48("event/oc/oc_loop.bccam");
        work->cam_start = engine_func_00263e48("event/oc/oc_start.bccam");
        work->model = engine_func_0029a2d0("event/oc/oc_loop.bam", 0x38);
        work->field_570 = 1;
    }

    // 0x002F645C..0x002F6464: return the singleton's task handle.
    return g_EventOpeningWork->calc_task;
}

// ---------------------------------------------------------------------------
// mapEpl.cpp (0x001FA408), 468 B
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x001fa408, 468)
void mapEpl_func_001fa408(u32 group, u32 index) {
    // 0x001FA41C..0x001FA49C: lazy construction of the 0x188-byte placement
    // manager.  The 0x10 records start at +0x08 and each one is 0x18 bytes.
    if (g_MapEplWork == nullptr) {
        MapEplWork* const created = static_cast<MapEplWork*>(
            AsdMem_Alloc(0x100, 0x100, 0, 0x188, 1));
        g_MapEplWork = created;
        created->field_00 = 0;                          // 0x001FA460
        created->field_04 = 0;                          // 0x001FA46C
        for (s32 i = 0; i < 0x10; ++i) {
            MapEplEntry* const entry = &created->entries[i];
            entry->pos[0] = 0.0f;                       // 0x001FA48C
            entry->pos[1] = 0.0f;
            entry->pos[2] = 0.0f;
            entry->rot = 0.0f;
            entry->resource = nullptr;                  // 0x001FA484
            entry->parts = nullptr;                     // 0x001FA488
        }
    }

    MapEplWork* const work = g_MapEplWork;

    // 0x001FA4A0..0x001FA4AC: an empty table skips the whole pass.  `fp` is the
    // "no free record" sentinel -1.
    if (engine_func_002fb3b8() <= 0) {
        return;
    }

    for (u32 row_index = 0;;) {
        const MapEplRow* const row = static_cast<const MapEplRow*>(
            engine_func_002c9ba4(row_index));           // 0x001FA4B8

        // 0x001FA4C0..0x001FA4DC: the -1 group is a terminator and both
        // selector bytes must match.
        if (row->group != -1 &&
            row->group == static_cast<s8>(group) &&
            row->index == static_cast<s8>(index)) {
            char path[0x80];
            UiText_Format(path, "effect_editor/%s.EPL",
                          row->name);                   // 0x001FA4EC

            // 0x001FA4F0..0x001FA51C: first record whose parts slot is empty.
            s32 slot = 0;
            while (slot < 0x10) {
                if (work->entries[slot].parts == nullptr) {
                    break;
                }
                ++slot;
            }

            if (slot == 0x10) {
                slot = -1;                              // 0x001FA520 `mov r4,fp`
            } else {
                // 0x001FA590..0x001FA5B4: load the EPL file and open the part
                // container into the chosen record.
                u32 size = 0;
                work->entries[slot].resource =
                    AsdFile_LoadSync(path, &size, 1, 0x80);
                work->entries[slot].parts = effParts_func_002a51dc(
                    reinterpret_cast<EffPartsSource*>(
                        work->entries[slot].resource));
            }

            // 0x001FA524..0x001FA56C: the guard reloads the +0x14 word through
            // `work + slot*0x18 + 0x1C`; with the -1 sentinel that address is
            // work+4 (cleared above), so a missing record silently skips.
            MapEplEntry* const entry = reinterpret_cast<MapEplEntry*>(
                reinterpret_cast<u8*>(work) +
                static_cast<std::ptrdiff_t>(slot) * 0x18 + 8);
            if (entry->parts != nullptr) {
                entry->rot = 0.0f;                      // 0x001FA564
                entry->pos[0] = static_cast<f32>(row->x); // 0x001FA568
                entry->pos[1] = static_cast<f32>(row->y);
                entry->pos[2] = static_cast<f32>(row->z);
                AsdPart_Setup2(entry->parts, entry->pos);
            }
        }

        // 0x001FA570..0x001FA580: the row count is re-read for every step.
        ++row_index;
        if (engine_func_002fb3b8() <= static_cast<s32>(row_index)) {
            break;
        }
    }
}

// ---------------------------------------------------------------------------
// mapMain.cpp (0x001B4410), 440 B
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x001b4410, 440)
void mapMain_func_001b4410() {
    MapMainWork* const work = static_cast<MapMainWork*>(
        AsdMem_Alloc(0x100, 0x100, 0, 0xC8, 1));        // 0x001B443C
    g_MapMainWork = work;                               // 0x001B4448

    u8* const engine = static_cast<u8*>(UiEngine_GetContext()); // 0x001B444C
    FrameTex_func_00280d30(1);                          // 0x001B4458

    work->field_00d = 0;                                // 0x001B4460
    work->field_00e = 0;                                // 0x001B4464
    work->field_00f = 0;                                // 0x001B4468
    work->field_010 = 0;                                // 0x001B446C
    work->field_011 = 0;                                // 0x001B4470
    work->field_012 = 0;                                // 0x001B4474
    work->field_013 = 0;                                // 0x001B4478
    work->field_014 = 0;                                // 0x001B447C
    work->field_018 = 0;                                // 0x001B4480
    work->field_01c = 0;                                // 0x001B4484
    work->field_01d = 0;                                // 0x001B4488
    work->field_01e = 0;                                // 0x001B448C
    work->field_01f = 0;                                // 0x001B4490
    work->field_020 = 0;                                // 0x001B4494
    work->field_03d = 0;                                // 0x001B4498
    work->field_040 = 0;                                // 0x001B449C
    work->field_024 = 0;                                // 0x001B44A0
    work->field_028 = 0;                                // 0x001B44A4 (`strd`)
    work->field_02c = 1;
    work->field_034 = 0;                                // 0x001B44A8
    work->field_030 = 1;                                // 0x001B44AC
    work->field_03c = 0;                                // 0x001B44B0
    work->field_047 = 1;                                // 0x001B44B4
    work->field_048 = 0;                                // 0x001B44B8
    work->field_046 = 0;                                // 0x001B44BC

    // 0x001B44C0..0x001B44D8: reset every map sub-manager.
    mapEpl_func_00192298();
    engine_func_001b4664();
    engine_func_001b3ca0();
    engine_func_00192320();
    engine_func_0018ab7c();
    engine_func_001923d0();
    engine_func_001a8b64();

    work->field_0a8 = 0x1C2;                            // 0x001B44E8 (`stm`)
    work->field_0ac = 0;
    work->field_0b4 = 0;                                // 0x001B44F4
    work->field_0b8 = 0;                                // 0x001B44F8
    work->field_0b9 = 0;                                // 0x001B44FC
    g_MapRuntimeState[0x22B] = 0;                       // 0x001B4500
    engine[0x790] = 0;                                  // 0x001B4504
    work->field_0c4 = 0;                                // 0x001B450C
    work->field_00c = 0;                                // 0x001B4514

    // 0x001B4508..0x001B452C: "MAP C" carries the FlowScript native-command
    // dispatcher (0x001B7E78) and user word 0x0020FD2C.
    work->calc_task = AsdTask_CreateCalc(
        "MAP C", 2, 0, 0, TaskCallback(0x001B7E78), 0x0020FD2C, 0);

    // 0x001B4534..0x001B4560: "MAP U" (0x6F) with callback 0x001E9414 and user
    // word 0x002CA688 under the calc task.
    work->draw_task = AsdTask_CreateDraw(
        "MAP U", 0x6F, 0, 0, TaskCallback(0x001E9414), 0x002CA688, 0,
        work->calc_task);
}

// ---------------------------------------------------------------------------
// naviMain.cpp (0x00291CAC), 412 B
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x00291cac, 412)
void naviMain_func_00291cac(u32 arg0, u32 arg1) {
    (void)arg0;                                         // r0 is never read

    NaviMainWork* const work = static_cast<NaviMainWork*>(
        AsdMem_Alloc(0x100, 0x100, 0, 0x12344, 1));     // 0x00291CDC
    g_NaviMainWork = work;                              // 0x00291CF0

    work->field_00a = 0;                                // 0x00291CF4
    work->field_009 = 0;                                // 0x00291CF8
    work->field_00c = 0;                                // 0x00291CFC
    work->field_010 = 0;                                // 0x00291D00
    work->field_014 = 0;                                // 0x00291D04
    work->field_018 = 0.0f;                             // 0x00291D08
    work->field_02c = 0;                                // 0x00291D0C
    work->field_028 = 1;                                // 0x00291D10
    work->field_034 = 1.0f;                             // 0x00291D14
    work->field_038 = 0.0f;                             // 0x00291D18
    work->field_03c = 0.0f;                             // 0x00291D1C
    work->field_008 = 0;                                // 0x00291D24

    // 0x00291D28..0x00291D44: the panel at +0x40, the common background, the
    // flag-0x16 script reset and the button help.
    engine_func_00399594(work->object_040);
    CommonBg_func_00289b4c();
    if (!Flag_CheckEventBit(0x16)) {                    // 0x00291D38..0x00291D40
        ScriptVm_func_00289ae8();
    }
    camp::ButtonHelp_Init();                            // 0x00291D44

    engine_func_00240e1c(arg1);                         // 0x00291D4C

    // 0x00291D50..0x00291D78: "NAVI PROC" calc task (0x001A95B8, user words
    // 0x001A959C and the work itself).
    work->proc_task = AsdTask_CreateCalc(
        "NAVI PROC", 2, 0, 0, TaskCallback(0x001A95B8), 0x001A959C,
        TaskUserData(work));

    // 0x00291D7C..0x00291DA4: "NAVI DOWN" (tag 0xE5) draw task.
    work->down_task = AsdTask_CreateDraw(
        "NAVI DOWN", 0xE5, 1, 0, TaskCallback(0x001FC480), 0,
        TaskUserData(work), work->proc_task);

    // 0x00291DA8..0x00291DD0: "NAVI FADE DRAW" (tag 0xE6) draw task; the
    // handle is kept at +0x12330.
    work->fade_task = AsdTask_CreateDraw(
        "NAVI FADE DRAW", 0xE6, 0, 0, TaskCallback(0x001FC454), 0, 0,
        work->proc_task);

    // 0x00291DD4..0x00291DE0: initialise the fade controller with mode 1.
    engine_func_003c2c58(&work->fade, 1);

    // 0x00291DE4..0x00291E08: start the fade with duration 0 and mode 0.
    if (g_NaviMainWork != nullptr) {
        engine_func_003c2c20(&g_NaviMainWork->fade, 0, 0);
    }
}

} // namespace smt4::engine

