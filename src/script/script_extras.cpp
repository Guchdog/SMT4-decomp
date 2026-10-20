#include "script/script_extras.h"
#include "engine/asd_symbols.h"
#include "engine/asd_frame.h"
#include "engine/asd_texture.h"
#include "ui/tbb_table.h"
#include "camp/unite.h"
#include <cstdint>

namespace smt4::script {

// ---------------------------------------------------------------------------
// Globals (addresses are the storage locations used by the listing)
// ---------------------------------------------------------------------------

NpcRoomWork* g_NpcRoomWork = nullptr;             // 0x0044D198 (BSS)
UIQuestWork* g_UIQuestWork = nullptr;             // 0x0043DD50 (BSS)
QcMainState g_QcMainState{0, nullptr, 1, 0, 0};   // 0x0044DB88 (.data)
EventCommandWork* g_EventCommandWork = nullptr;   // 0x0043E088 (BSS)
EventEffectWork* g_EventEffectWork = nullptr;     // 0x0043DEE8 (BSS)
ClearSaveWork* g_ClearSaveWork = nullptr;         // 0x0043DE80 (BSS)
ScrScriptProcessList g_ScrScriptProcessList{};    // 0x0044DE78 (.data, all zero)

// 0x0043DF00 (.data): two {key 0x2D, row 4/6} texture rows.
BlinkFadeTexture g_BlinkFadeTextures[2] = {
    {0x2D, 4, 0, 0},
    {0x2D, 6, 0, 0},
};

// ---------------------------------------------------------------------------
// Observed call targets (addresses are the branch targets in code.bin)
// ---------------------------------------------------------------------------

extern "C" {
    // AsdMemory (c:\SMT4\XRD686\AsdSDK\Source\Sys\Mem\AsdMemory.cpp)
    void* AsdMem_Alloc(u32 a0, u32 a1, u32 a2, u32 size, u32 flag);        // 0x002C4B84
    void* AsdMem_AllocAlign(u32 a0, u32 a1, u32 a2, u32 size, u32 flag);   // 0x002C54F0
    void  AsdMem_Zero(void* ptr, u32 size);                                // 0x002C4B30
    void  AsdMem_Free(void* ptr);                                          // 0x002C4360

    // 0x002C32F8 / 0x002C3344: 32-byte layout descriptor helpers.  The
    // eleven-argument shape is the one used by battle_extras.cpp; the last
    // seven words are the r1/r2/r3 + stack words observed at the call site.
    void UiSpriteGroup_Init(void* group);                                  // 0x002C3344
    void UiSpriteGroup_BindTable(void* group, u32 a1, u32 a2, u32 a3,
                                 u32 a4, u32 a5, u32 a6, u32 a7, u32 a8,
                                 u32 a9, u32 a10);                         // 0x002C32F8

    // 0x002BDB2C (sprite,type,id,group,flag,scale) and its 0x002BF0A8
    // variant with an explicit mode word before the group pointer.
    void UiAnimSprite_Setup(void* sprite, s32 type, s32 id, void* group,
                            u32 flag, f32 scale);                          // 0x002BDB2C
    void UiAnimSprite_SetupEx(void* sprite, s32 type, s32 id, u32 mode,
                              void* group, u32 flag, f32 scale);           // 0x002BF0A8
    void UiAnimSprite_SetAnim(void* sprite, s32 anim, s32 mode);           // 0x002BDAC0
    void UiAnimSprite_SetLayer(void* sprite, s32 layer);                   // 0x002BF030
    void UiAnimSprite_SetText(void* sprite, s32 a1, s32 a2);               // 0x00296154
    void UiAnimSprite_SetPos(void* sprite, s32 x, s32 y);                  // 0x002B2808

    // 0x002976AC: lazily resolves one 0x0049382C resource-table slot; returns
    // 1 when the slot is resident (or already marked unresolvable).
    u32  CampRes_LoadEntry(u32 id);

    // 0x002C5E2C: 16-byte resource loader wrapper; the callers use the return
    // value as the 32-bit .bf/.mbm handle.
    void* ScriptRes_Load(const char* name);

    void  CommonBg_func_00289b4c();                                       // 0x00289B4C
    void  ScriptVm_func_00289ae8();                                       // 0x00289AE8
    void  ScriptVm_func_00291000(u32 value);                              // 0x00291000

    // 0x001AD8D4: writes the low byte into manager + 0x10.
    void  QuestUi_SetVisible(u8 visible);

    // Quest flag helpers used by the two 0x190-entry sweeps.
    u32   QuestStatus_Get(u32 index, u32 kind);                           // 0x0029923C
    u32   QuestFlag_Get7(u32 index);                                      // 0x00299224
    u32   QuestFlag_Get20(u32 index);                                     // 0x00288930
    u32   QuestFlag_Get40(u32 index);                                     // 0x00288918
    void  QuestFlags_Clear60(u32 index);                                  // 0x002543D8
    void  QuestUi_Reset();                                                // 0x00189B24

    // 0x00296154 companion that needs one extra pair of coordinates.
    void  QuestUi_SetTextPair(void* sprite, s32 a1, s32 a2, s32 a3);      // 0x00262448

    // TBB/resource row helpers reached from the 2D NPC and BlinkFade paths.
    int   AsdTMTexTable_IsGroupLoaded(u32 group_id);                      // 0x0024BD24
    int   AsdRes_IsLoaded(u32 key, u32 sub);                              // 0x002A63F8
    void  AsdRes_Request(u32 key, u32 sub);                               // 0x002A6214
    void* AsdRow_LoadNow(u32 key, u32 sub);                               // 0x002C5AB8

    // qcUtility / qcMain helpers.
    u32   QcTable_GetRowCount(void* context, u32 category);               // 0x003EA530
    const u8* QcTable_GetRows(void* context, u32 category, u32 row);      // 0x00235758
    s32   QcSave_CountCompleted();                                        // 0x00348D84
    u16   QcProgress_Get14();                                             // 0x00343CD4
    u16   QcProgress_Get16();                                             // 0x00343C9C
    u16   QcProgress_Get18();                                             // 0x00343E00
    u16   QcProgress_Get1a();                                             // 0x00343C8C
    u32   Random_Range(u32 range_plus_one);                               // 0x002C0BCC
    void  QcMain_SetTab(s32 value, s32 mode);                             // 0x00343D94
    void  QcMain_SetFlag(u32 flag, u32 value, u32 mode);                  // 0x002899C4
    void  ClearSave_SetFade(u32 index, u32 value);                        // 0x00282E6C
    void  Npc2d_SetPose(void* sprite, s32 pose);                          // 0x002FDFA4

}

static inline void (*TaskCallback(u32 address))(void*) {
    return reinterpret_cast<void (*)(void*)>(
        static_cast<std::uintptr_t>(address));
}

static inline u32 TaskUserData(const void* pointer) {
    return static_cast<u32>(reinterpret_cast<std::uintptr_t>(pointer));
}

// ---------------------------------------------------------------------------
// NpcRoom.cpp (0x0026DF40), 1,620 B
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x0026df40, 1620)
void NpcRoom_func_0026df40(u32 room_id) {
    const u16 id = static_cast<u16>(room_id);

    if (g_NpcRoomWork == nullptr) {
        // 0x0026DF5C..0x0026DF80: 0x100/0x100/0/0x108/1; the ADR string and
        // line 0x1C8 are the dead debug arguments of the allocation macro.
        g_NpcRoomWork = static_cast<NpcRoomWork*>(
            AsdMem_Alloc(0x100, 0x100, 0, sizeof(NpcRoomWork), 1));
    }
    NpcRoomWork* work = g_NpcRoomWork;
    AsdMem_Zero(work, sizeof(NpcRoomWork));                 // 0x0026DF8C

    work->calc_task = AsdTask_CreateCalc("NpcRoom Calc", 2, 0, 0,
                                         TaskCallback(0x0019416C), 0, 0);
    void* parent = work->calc_task;                         // 0x0026DFBC

    // 0x0026DFC0..0x0026E028: three draw tasks sharing the calc task as
    // parent.  The down-draw callback is the command 0x001DD7E0.
    AsdTask_CreateDraw("NpcRoom UDrawLeft", 0x7A, 0, 0,
                       TaskCallback(0x001AB940), 0, 0, parent);
    AsdTask_CreateDraw("NpcRoom UDrawRight", 0xD8, 0, 0,
                       TaskCallback(0x001AB940), 0, 0, parent);
    AsdTask_CreateDraw("NpcRoom DDraw", 0xE6, 0, 0,
                       TaskCallback(0x001DD7E0), 0, 0, parent);

    // 0x0026E02C..0x0026E040: resource slots 0x35 and 0x1A.
    CampRes_LoadEntry(0x35);
    CampRes_LoadEntry(0x1A);

    work->room_id = id;                                     // `strh r6,[sl]`
    work->current = nullptr;                                // `str fp,[r7,#0x24]`

    // 0x0026E054..0x0026E0A4: first table (slot 0x35, table 0) holds the
    // 0x6C-byte room rows; the matching row becomes the current NPC entry.
    {
        const ui::Tbl1Header* table = ui::Tbb_GetGlobalSubTable(0x35, 0);
        const u8* row = static_cast<const u8*>(ui::Tbb_GetPayloadData(table));
        const u32 count = ui::Tbb_GetRowCount(table);
        for (u32 i = 0; i < count; ++i, row += sizeof(NpcRoomRow)) {
            if (reinterpret_cast<const NpcRoomRow*>(row)->room_id == id) {
                work->current = reinterpret_cast<const NpcRoomEntry*>(row);
                break;
            }
        }
    }

    // 0x0026E0A8..0x0026E160: second table (slot 0x35, table 1) holds the
    // 0xD4-byte NPC rows.  A row is accepted only when its four optional
    // event bits have the required polarity.
    work->entries[0] = nullptr;
    work->entries[1] = nullptr;
    work->entries[2] = nullptr;
    work->entries[3] = nullptr;
    work->entry_count = 0;
    {
        const ui::Tbl1Header* table = ui::Tbb_GetGlobalSubTable(0x35, 1);
        const u8* row = static_cast<const u8*>(ui::Tbb_GetPayloadData(table));
        const u32 count = ui::Tbb_GetRowCount(table);
        for (u32 i = 0; i < count; ++i, row += sizeof(NpcRoomEntry)) {
            const NpcRoomEntry* entry = reinterpret_cast<const NpcRoomEntry*>(row);
            if (entry->room_id != id) {
                continue;
            }
            if (entry->flag_a != 0 && !Flag_CheckEventBit(entry->flag_a)) {
                continue;
            }
            if (entry->flag_b != 0 && !Flag_CheckEventBit(entry->flag_b)) {
                continue;
            }
            if (entry->flag_c != 0 && Flag_CheckEventBit(entry->flag_c)) {
                continue;
            }
            if (entry->flag_d != 0 && Flag_CheckEventBit(entry->flag_d)) {
                continue;
            }
            work->entries[work->entry_count] = entry;
            ++work->entry_count;
            if (work->entry_count >= 8) {
                break;                                      // 0x0026E18C
            }
        }
    }

    // 0x0026E1A4..0x0026E1C0: all eight visible records become 0xFFFF.
    for (s32 i = 0; i < 8; ++i) {
        AsdMem_FillBytes(&work->visible[i], sizeof(NpcRoomVisible), 0xFF);
    }

    // 0x0026E1C4..0x0026E434: group the accepted entries by +0x0A.  The
    // first entry of each group goes into visible[count].entries[0]; every
    // later entry of the same group is appended to that record.  The local
    // u16[8] at sp+0x10 holds each group's type (0x0026E428).
    u16 group_types[8] = {0, 0, 0, 0, 0, 0, 0, 0};
    work->visible_count = 0;
    for (s32 i = 0; i < 8; ++i) {
        const NpcRoomEntry* entry = work->entries[i];
        if (entry == nullptr) {
            continue;                                       // 0x0026E1F0
        }
        const u16 type = entry->group_type;
        if (type == 0) {
            work->visible[work->visible_count].entries[0] =
                static_cast<u16>(i);
            ++work->visible_count;                          // 0x0026E22C
            continue;
        }

        bool seen = false;
        for (s32 j = 0; j < i; ++j) {
            if (group_types[j] == type) {
                seen = true;
                break;
            }
        }
        if (seen) {
            continue;                                       // 0x0026E320
        }

        NpcRoomVisible* record = &work->visible[work->visible_count];
        record->entries[0] = static_cast<u16>(i);           // 0x0026E330
        s32 slot = 1;                                        // r0
        const s32 remaining = static_cast<s32>(work->entry_count) - i;
        if (remaining > 1) {
            // The listing unrolls the scan in pairs (0x0026E348..0x0026E408);
            // `slot` is the r0 write cursor, `index` the ip scan offset.
            s32 index;
            if ((remaining & 1) == 0) {
                if (work->entries[i + 1]->group_type == type) {
                    record->entries[slot++] = static_cast<u16>(i + 1);
                }
                index = 1;
            } else {
                index = 0;
            }
            const s32 pairs = (remaining - 1) >> 1;
            for (s32 pair = 0; pair < pairs; ++pair) {
                if (work->entries[i + index]->group_type == type) {
                    record->entries[slot++] =
                        static_cast<u16>(i + index + 1);
                }
                if (work->entries[i + index + 1]->group_type == type) {
                    record->entries[slot++] =
                        static_cast<u16>(i + index + 2);
                }
                index += 2;
            }
        }
        group_types[i] = type;                              // 0x0026E428
        ++work->visible_count;                              // 0x0026E41C
    }

    // 0x0026E438..0x0026E478: message/script resources and two script
    // processes, each put into state 2.
    work->msg_mbm = static_cast<u32>(
        reinterpret_cast<std::uintptr_t>(ScriptRes_Load("npc_room/npcMsg.mbm")));
    work->script_bf = static_cast<u32>(
        reinterpret_cast<std::uintptr_t>(ScriptRes_Load("npc_room/npc.bf")));
    work->script_process_a = scrScriptProcess_func_002972f8(
        reinterpret_cast<void*>(static_cast<std::uintptr_t>(work->script_bf)),
        reinterpret_cast<void*>(static_cast<std::uintptr_t>(work->msg_mbm)));
    static_cast<ScrScriptProcess*>(work->script_process_a)->state = 2;
    work->script_process_b = scrScriptProcess_func_002972f8(
        reinterpret_cast<void*>(static_cast<std::uintptr_t>(work->script_bf)),
        reinterpret_cast<void*>(static_cast<std::uintptr_t>(work->msg_mbm)));
    static_cast<ScrScriptProcess*>(work->script_process_b)->state = 2;

    // 0x0026E47C..0x0026E4F4: create and attach each NPC sprite.  `variant`
    // selects the 0x002523D0 / 0x002860B4 constructor; the pose is the row's
    // +0x0D byte plus 3.
    for (s32 i = 0; i < 8; ++i) {
        const NpcRoomEntry* entry = work->entries[i];
        if (entry == nullptr) {
            continue;                                       // 0x0026E48C
        }
        const s32 y = entry->offset_y + entry->offset_x;
        void* sprite;
        if (entry->variant != 0) {
            sprite = engine::Npc2d_func_002523d0(entry->sprite_id, 0, y);
        } else {
            sprite = engine::Npc2d_func_002860b4(entry->sprite_id, 0, y);
        }
        work->sprites[i] = sprite;
        AsdProc_Attach(work->calc_task, sprite);            // 0x0026E4D4
        Npc2d_SetPose(sprite, entry->pose + 3);             // 0x0026E4E8
    }

    // 0x0026E4F8..0x0026E534: select the row in TBB slot 0x1A from the
    // current room entry's +0x22 index (one-based).
    {
        const ui::Tbl1Header* table = ui::Tbb_GetGlobalSubTable(0x1A, 0);
        const u8* payload =
            static_cast<const u8*>(ui::Tbb_GetPayloadData(table));
        (void)ui::Tbb_GetRowCount(table);
        const u16 index = work->current->payload_index;
        const u16 row = *reinterpret_cast<const u16*>(
            payload + static_cast<std::uintptr_t>(index) * 2 - 2);
        work->payload_row = row;                            // 0x0026E530
        AsdRow_LoadNow(2, row);                     // 0x0026E534
    }

    CommonBg_func_00289b4c();                               // 0x0026E540
    ScriptVm_func_00289ae8();                               // 0x0026E54C
    camp::ButtonHelp_Init();                                // 0x0026E558
    ScriptVm_func_00291000(0xA0);                           // 0x0026E564
}

// ---------------------------------------------------------------------------
// UIQuest.cpp (0x0026A02C), 1,412 B
// ---------------------------------------------------------------------------

static inline void* UiQuest_Sprite(UIQuestWork* work, u32 index) {
    return work->sprites + static_cast<std::uintptr_t>(index) * 0x8C;
}

// DECOMP_FUNC(0x0026a02c, 1412)
void UIQuest_func_0026a02c() {
    if (g_UIQuestWork == nullptr) {
        // 0x0026A04C..0x0026A070: 0x100/0x100/0/0x9FC/1.
        g_UIQuestWork = static_cast<UIQuestWork*>(
            AsdMem_Alloc(0x100, 0x100, 0, sizeof(UIQuestWork), 1));
    }
    UIQuestWork* work = g_UIQuestWork;
    AsdMem_Zero(work, sizeof(UIQuestWork));                 // 0x0026A080

    work->calc_task = AsdTask_CreateCalc("UIQuest Calc", 2, 0, 0,
                                         TaskCallback(0x001955BC), 0, 0);
    void* parent = work->calc_task;
    AsdTask_CreateDraw("UIQuest UDrawLeft", 0x7D, 0, 0,
                       TaskCallback(0x001AD8EC), 0, 0, parent);
    AsdTask_CreateDraw("UIQuest UDrawRight", 0xDB, 0, 0,
                       TaskCallback(0x001AD8EC), 0, 0, parent);
    AsdTask_CreateDraw("UIQuest DDraw", 0xE6, 0, 0,
                       TaskCallback(0x001DDB74), 0, 0, parent);

    // 0x0026A11C..0x0026A150: quest resources and one script process.
    work = g_UIQuestWork;
    QuestUi_SetVisible(0);
    work->msg_mbm = static_cast<u32>(reinterpret_cast<std::uintptr_t>(
        ScriptRes_Load("event/quest/QuestSys.mbm")));
    work->script_bf = static_cast<u32>(reinterpret_cast<std::uintptr_t>(
        ScriptRes_Load("event/quest/QuestScr.bf")));
    work->script_process = scrScriptProcess_func_002972f8(
        reinterpret_cast<void*>(static_cast<std::uintptr_t>(work->script_bf)),
        reinterpret_cast<void*>(static_cast<std::uintptr_t>(work->msg_mbm)));
    work->field_982 = 0;
    work->field_984 = 0;

    // 0x0026A158..0x0026A184: texture group 0x29, row 0, resource 0x34 and
    // the quest list reset.
    engine::AsdTMTexTable_func_002c4e28(0x29);
    AsdRow_LoadNow(0x29, 0);
    CampRes_LoadEntry(0x34);
    QuestUi_Reset();

    // 0x0026A188..0x0026A264: two sweeps over quest ids 0..0x18F.  The
    // first clears bit pair 0x60 for "accepted" records, the second for
    // records whose +7 bit is clear.
    for (u16 i = 0; i < 0x190; ++i) {
        if (QuestStatus_Get(i, 2) == 0) {
            continue;
        }
        if (QuestFlag_Get7(i) == 0) {
            continue;
        }
        if (QuestFlag_Get20(i) != 0 || QuestFlag_Get40(i) != 0) {
            QuestFlags_Clear60(i);
        }
    }
    for (u16 i = 0; i < 0x190; ++i) {
        if (QuestStatus_Get(i, 2) == 0) {
            continue;
        }
        if (QuestFlag_Get7(i) != 0) {
            continue;
        }
        if (QuestFlag_Get20(i) != 0 || QuestFlag_Get40(i) != 0) {
            QuestFlags_Clear60(i);
        }
    }

    // 0x0026A268..0x0026A2AC: 0x20-byte layout descriptor at +0x14.  The
    // eleven arguments map to (r1,r2,r3,stack0..stack6) of 0x002C32F8.
    UiSpriteGroup_Init(&work->layout);                      // 0x002C3344
    UiSpriteGroup_BindTable(&work->layout,
                            0x00402E54, 0x3C, 0x00402E90,
                            0x60, 0x00402EF0, 0x3C, 0, 0,
                            0x00402F2C, 0x214);             // 0x002C32F8

    // 0x0026A2B0..0x0026A334: sprites 0..2 (type 0x29, flag 0xC9).
    UiAnimSprite_Setup(UiQuest_Sprite(work, 0), 0x29, 0, &work->layout,
                       0xC9, 1.0f);
    UiAnimSprite_SetAnim(UiQuest_Sprite(work, 0), 0, 0);
    UiAnimSprite_Setup(UiQuest_Sprite(work, 1), 0x29, 0, &work->layout,
                       0xC9, 1.0f);
    UiAnimSprite_SetLayer(UiQuest_Sprite(work, 1), 0);
    UiAnimSprite_Setup(UiQuest_Sprite(work, 2), 0x29, 0, &work->layout,
                       0xC9, 1.0f);
    UiAnimSprite_SetAnim(UiQuest_Sprite(work, 2), 4, 0);

    // 0x0026A338..0x0026A38C: sprite 3 and sprite 4 (id 0x61, flag 0x68).
    UiAnimSprite_Setup(UiQuest_Sprite(work, 3), 0x29, 0, &work->layout,
                       0xC9, 1.0f);
    UiAnimSprite_Setup(UiQuest_Sprite(work, 4), 0x29, 0x61, &work->layout,
                       0x68, 1.0f);
    UiAnimSprite_SetLayer(UiQuest_Sprite(work, 4), 2);
    UiAnimSprite_SetText(UiQuest_Sprite(work, 4), 0x29, 0x2A);

    // 0x0026A390..0x0026A3C8: sprite 5 (id 0x5D, flag 0xA1).
    UiAnimSprite_Setup(UiQuest_Sprite(work, 5), 0x29, 0x5D, &work->layout,
                       0xA1, 1.0f);
    UiAnimSprite_SetLayer(UiQuest_Sprite(work, 5), 2);
    UiAnimSprite_SetText(UiQuest_Sprite(work, 5), 0x29, 0x53);

    // 0x0026A3CC..0x0026A410: sprite 6 uses the mode-bearing setup, then
    // stores halfword 2 at +0x3A and the coordinate pair (0,0x78).
    UiAnimSprite_SetupEx(UiQuest_Sprite(work, 6), 0x29, -1, 0x12,
                         &work->layout, 0xC9, 1.0f);
    UiAnimSprite_SetLayer(UiQuest_Sprite(work, 6), 3);
    *reinterpret_cast<u16*>(
        static_cast<u8*>(UiQuest_Sprite(work, 6)) + 0x3A) = 2;
    UiAnimSprite_SetPos(UiQuest_Sprite(work, 6), 0, 0x78);

    // 0x0026A4F4..0x0026A534: sprite 7 (id 0x5C, flag 0xA1).
    UiAnimSprite_Setup(UiQuest_Sprite(work, 7), 0x29, 0x5C, &work->layout,
                       0xA1, 1.0f);
    UiAnimSprite_SetAnim(UiQuest_Sprite(work, 7), 0, 0);
    QuestUi_SetTextPair(UiQuest_Sprite(work, 7), 0x29, 0x5A, 0x5C);

    // 0x0026A538..0x0026A58C: sprites 8 and 9.
    UiAnimSprite_Setup(UiQuest_Sprite(work, 8), 0x29, 0, &work->layout,
                       0xC9, 1.0f);
    UiAnimSprite_SetAnim(UiQuest_Sprite(work, 8), 2, 0);
    UiAnimSprite_Setup(UiQuest_Sprite(work, 9), 0x29, 0, &work->layout,
                       0xC9, 1.0f);
    UiAnimSprite_SetLayer(UiQuest_Sprite(work, 9), 5);

    // 0x0026A590..0x0026A5A0: re-read the singleton and shift the two task
    // pointers: +4 = 0, +8 = old +4, +0x10 = 0.
    work = g_UIQuestWork;
    void* old = work->draw_up_left;
    work->draw_up_left = nullptr;
    work->draw_up_right = old;
    work->field_010 = 0;
}

// ---------------------------------------------------------------------------
// qcUtility.cpp (0x003816E4), 1,012 B
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x003816e4, 1012)
u32 qcUtility_func_003816e4(void* state, u32 block, void* context,
                            s32 selected, u32 ext_offset,
                            s32 min_index, s32 max_index) {
    // 0x003816EC..0x00381730: block base = state + block*0x50; the 20 s32
    // selection slots start at +0x10 and are all set to -2.
    u8* const block_base = static_cast<u8*>(state) +
                           static_cast<std::uintptr_t>(block) * 0x50;
    QcUtilityBlock* const header =
        reinterpret_cast<QcUtilityBlock*>(block_base);
    s32* const slots = reinterpret_cast<s32*>(block_base + 0x10);
    for (s32 i = 0; i < 20; ++i) {
        slots[i] = -2;
    }

    // 0x00381734..0x00381770: row count and the 8-byte output array.
    const s32 row_count =
        static_cast<s32>(QcTable_GetRowCount(context, header->category));
    QcListEntry* out = static_cast<QcListEntry*>(
        AsdMem_AllocAlign(0x100, 0x100, 0,
                          static_cast<u32>(row_count) * sizeof(QcListEntry),
                          1));
    const u8* rows = QcTable_GetRows(context, header->category, 0);

    // 0x00381778..0x00381814: filter rows with a non-zero quantity byte and
    // an unset (or satisfied) event flag, then accumulate the quantities.
    s32 count = 0;                                          // r5
    s32 total = 0;                                          // fp
    for (s32 i = 0; i < row_count; ++i) {
        const u8* row = rows + static_cast<std::uintptr_t>(i) * 0x20;
        const u8* extended = row + static_cast<std::uintptr_t>(ext_offset);
        if (extended[0x1A] == 0) {
            continue;
        }
        const u16 flag = *reinterpret_cast<const u16*>(row + 0x18);
        if (flag != 0 && Flag_CheckEventBit(flag)) {
            continue;
        }
        out[count].index = static_cast<u16>(i);             // 0x003817E8
        out[count].value = *reinterpret_cast<const u16*>(row + 0x16);
        out[count].quantity = extended[0x1A];               // 0x00381804
        ++count;
        total += extended[0x1A];
    }

    // 0x00381818..0x0038186C: if the block names a target row, pin it into
    // slot 0 and remove its quantity from the pool.
    if (header->target_index != 0 && count > 0) {
        for (s32 i = 0; i < count; ++i) {
            if (out[i].value == header->target_index) {
                slots[0] = out[i].index;
                total -= static_cast<s32>(out[i].quantity);
                out[i].quantity = 0;
                break;
            }
        }
    }

    // 0x00381870..0x00381970: progress budget.  The four getters read the
    // u16 at object+0x14/+0x16/+0x18/+0x1A; the 0x66666667 magic performs
    // signed /10 (shift 2) or /20 (shift 3).
    const s32 completed = QcSave_CountCompleted();
    s32 budget;
    switch (block) {
        case 0: {
            budget = QcProgress_Get14() / 20 + completed / 10;
            break;
        }
        case 1: {
            const s32 value = QcProgress_Get16();
            budget = value / 10 + completed / 10;
            if (value < 10) {
                budget = 0;
            }
            break;
        }
        case 2: {
            const s32 value = QcProgress_Get18();
            budget = value / 10 + completed / 10;
            if (value < 10) {
                budget = 0;
            }
            break;
        }
        case 3: {
            const s32 value = QcProgress_Get1a();
            budget = value / 10 + completed / 10;
            if (value < 10) {
                budget = 0;
            }
            break;
        }
        default:
            budget = 0;
            break;
    }
    if (budget > 0x50) {
        budget = 0x50;                                      // 0x00381970
    }

    // 0x00381974..0x00381AC0: fill the 20 selection slots.
    u32 result = 0;                                         // sp+4
    bool chose = false;                                     // sl
    for (s32 i = 0; i < 20; ++i) {
        if (slots[i] != -2) {
            continue;
        }

        bool take = false;
        if (selected >= 0) {
            // 0x00381990..0x003819A4: explicit selection wins.
            take = (selected == i);
        } else {
            // 0x003819A8..0x003819E4: range and progress checks.
            take = (chose == false);
            if (take && i < min_index) {
                take = false;
            }
            if (take && i > max_index) {
                take = false;
            }
            if (take && i == max_index) {
                // `beq 0x003819E8` accepts the last in-range slot.
            } else if (take) {
                if (budget == 0) {
                    take = false;
                } else if (Random_Range(0x63) >=
                           static_cast<u32>(budget)) {
                    take = false;
                }
            }
        }

        if (take) {
            // 0x003819E8..0x003819F4.
            chose = true;
            slots[i] = -1;
            result = 1;
            continue;
        }

        // 0x003819F8..0x00381AB4: fallback draw from the remaining quantity
        // pool.  Types 3/4/5 may only fill slots strictly inside the range.
        const u32 pick = Random_Range(static_cast<u16>(total));
        for (s32 j = 0; j < count; ++j) {
            QcListEntry* entry = &out[j];
            if (entry->quantity == 0) {
                continue;
            }
            if (static_cast<s32>(pick) - static_cast<s32>(entry->quantity) > 0) {
                continue;
            }
            const u16 type = entry->value;
            if (type == 3 || type == 4 || type == 5) {
                if (!(min_index < i && i < max_index)) {
                    continue;
                }
            }
            slots[i] = entry->index;                        // 0x00381A4C
            total -= static_cast<s32>(entry->quantity);
            entry->quantity = 0;                            // 0x00381A54
            break;
        }
    }

    AsdMem_Free(out);                                       // 0x00381AC8
    return result;
}

// ---------------------------------------------------------------------------
// scrScriptProcess.cpp (0x002972F8), 892 B
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x002972f8, 892)
ScrScriptProcess* scrScriptProcess_func_002972f8(void* script, void* msg) {
    ScrScriptProcess* process = nullptr;
    u8* const base = static_cast<u8*>(script);
    u8* const commands = base + 0x20;                       // r6

    // 0x0029730C..0x00297340: require the "FLW0" magic at +8.
    if (base[8] != 0x46 || base[9] != 0x4C ||
        base[10] != 0x57 || base[11] != 0x30) {
        return nullptr;
    }

    // 0x00297344..0x002973B0: walk the 0x10-byte descriptors.  Types 0/1/2/4
    // select the name, value, second-value and extra offsets; type 3 is
    // ignored (`83` table entry falls through to the loop increment).
    u32 name_offset = 0;                                    // r7
    u32 value_offset = 0;                                   // sl
    u32 second_offset = 0;                                  // r8
    u32 extra_offset = 0;                                   // ip
    const s32 descriptor_count =
        *reinterpret_cast<const s32*>(base + 0x10);
    for (s32 i = 0; i < descriptor_count; ++i) {
        const ScrScriptDescriptor* desc =
            reinterpret_cast<const ScrScriptDescriptor*>(commands + i * 0x10);
        if (desc->type >= 5) {
            continue;
        }
        switch (desc->type) {
            case 0: name_offset = desc->offset; break;      // 0x0029737C
            case 1: value_offset = desc->offset; break;     // 0x00297388
            case 2: second_offset = desc->offset; break;    // 0x00297394
            case 4: extra_offset = desc->offset; break;     // 0x002973A0
            default: break;                                 // type 3
        }
    }

    // 0x002973B4..0x002973DC: the script must expose a name, a value table
    // and a positive count at +0x28.
    if (script == nullptr || commands == nullptr ||
        name_offset == 0 || second_offset == 0 ||
        *reinterpret_cast<const s32*>(commands + 8) <= 0) {
        return nullptr;
    }

    // 0x002973E0..0x00297418: 0x100/0x100/0/0x10C/0.
    process = static_cast<ScrScriptProcess*>(
        AsdMem_AllocAlign(0x100, 0x100, 0, sizeof(ScrScriptProcess), 0));
    AsdMem_Zero(process, sizeof(ScrScriptProcess));
    if (process == nullptr) {
        return nullptr;
    }

    // 0x0029741C..0x00297434: copy the NUL-terminated name from the first
    // descriptor payload.  `sb` stays zero, so the source is base+name_offset.
    {
        const char* source = reinterpret_cast<const char*>(base + name_offset);
        char* dst = process->name;
        while ((*dst++ = *source++) != '\0') {
        }
    }

    // 0x00297438..0x0029746C: payload word +0x18 and the zeroed block at
    // +0x3C (0x70 bytes).
    process->field_018 =
        *reinterpret_cast<const s32*>(base + name_offset + 0x18);
    process->field_01c = 0;
    process->field_020 = 0;
    process->field_024 = 0;
    process->field_028 = 0;
    process->field_02c = 0;
    process->field_030 = 0;
    process->field_034 = 0;
    process->field_038 = 0;
    AsdMem_Zero(process->block_03c, sizeof(process->block_03c));

    // 0x00297470..0x002974B0: script/command/value pointers and zeroed
    // runtime words.
    process->script = script;
    process->commands = commands;
    process->offset_name = name_offset;
    process->offset_sl = value_offset;
    process->offset_r8 = second_offset;
    process->msg = msg;
    process->offset_ip = extra_offset;
    process->field_0c8 = 0;
    process->field_0cc = 0;
    process->field_0d0 = 0;
    process->field_0d4 = 0;
    process->field_0d8 = 0;
    process->field_0dc = 0;
    process->field_0e0 = 0;
    process->field_0e4 = 0;
    process->values = nullptr;
    process->floats = nullptr;
    process->prev = nullptr;
    process->next = nullptr;

    // 0x002974B4..0x00297540: s32 array of script+0x14 entries, all zero.
    const s32 value_count = *reinterpret_cast<const s16*>(base + 0x14);
    if (value_count <= 0) {
        process->values = nullptr;
    } else {
        process->values = static_cast<s32*>(
            AsdMem_AllocAlign(0x100, 0x100, 0, value_count * 4, 0));
        for (s32 i = 0; i < value_count; ++i) {
            process->values[i] = 0;
        }
    }

    // 0x00297544..0x002975E0: f32 array of script+0x16 entries, all 0.0f.
    const s32 float_count = *reinterpret_cast<const s16*>(base + 0x16);
    if (float_count <= 0) {
        process->floats = nullptr;
    } else {
        process->floats = static_cast<f32*>(
            AsdMem_AllocAlign(0x100, 0x100, 0, float_count * 4, 0));
        for (s32 i = 0; i < float_count; ++i) {
            process->floats[i] = 0.0f;
        }
    }

    // 0x002975E4..0x0029760C: append to the global process list.  The first
    // node is both head and tail; later nodes become the new tail.
    ScrScriptProcess* const old_tail = g_ScrScriptProcessList.tail;
    if (old_tail == nullptr) {
        g_ScrScriptProcessList.head = process;
        g_ScrScriptProcessList.tail = process;
        process->prev = nullptr;
        process->next = nullptr;
    } else {
        process->prev = old_tail;
        old_tail->next = process;
        process->next = nullptr;
        g_ScrScriptProcessList.tail = process;
    }
    ++g_ScrScriptProcessList.count;

    return process;                                         // 0x00297614
}

// ---------------------------------------------------------------------------
// qcMain.cpp (0x001A969C), 644 B
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x001a969c, 644)
void qcMain_func_001a969c(const u32* args, u32 mode) {
    // 0x001A96AC: table slot 0 is fetched and discarded.
    (void)AsdSound_GetTableEntry(0);

    // 0x001A96B4..0x001A96F8: 0x20-byte workspace; +0x18/+0x19/+0x1C are
    // cleared, the remaining words are left as allocated.
    QcMainWork* work = static_cast<QcMainWork*>(
        AsdMem_Alloc(0x100, 0x100, 0, sizeof(QcMainWork), 1));
    g_QcMainState.work = work;
    work->flag_18 = 0;
    work->field_1c = 0;
    work->flag_19 = 0;

    if (args != nullptr) {
        // 0x001A9700..0x001A9740: mode 0x0C copies three words, mode 4
        // copies one word and clears the other two.
        if (mode == 0x0C) {
            const s32 first = static_cast<s32>(args[0]);
            if (first != -1) {
                g_QcMainState.field_08 = first;
            }
            g_QcMainState.field_0c = static_cast<s32>(args[1]);
            g_QcMainState.field_10 = static_cast<s32>(args[2]);
        } else if (mode == 4) {
            g_QcMainState.field_08 = static_cast<s32>(args[0]);
            g_QcMainState.field_0c = 0;
            g_QcMainState.field_10 = 0;
        }
        QcMain_SetTab(g_QcMainState.field_08, 1);           // 0x001A974C
    } else {
        // 0x001A975C..0x001A97AC: default tab/flag bootstrap.
        g_QcMainState.field_0c = 0;
        g_QcMainState.field_10 = 1;
        QcMain_SetFlag(0x50, 1, 1);
        QcMain_SetFlag(0x20, 1, 1);
        QcMain_SetFlag(0x5F, 1, 1);
        QcMain_SetFlag(0x143, 1, 1);
        QcMain_SetFlag(0x157, 1, 1);
    }

    // 0x001A97B0..0x001A987C: calc task plus four draw tasks.  The first and
    // last handles are kept at +0x04/+0x0C; the middle two are discarded.
    work->calc_task = AsdTask_CreateCalc("QuestCenterMainProc", 2, 0, 0,
                                         TaskCallback(0x001A9970),
                                         0x001FE0B4, TaskUserData(work));
    AsdTask_CreateDraw("QuestCenterDrawUp L", 0x6F, 1, 0,
                       TaskCallback(0x001FE134), 0,
                       TaskUserData(work), work->calc_task);
    work->draw_up = AsdTask_CreateDraw("QuestCenterDrawUp L", 0x7D, 1, 0,
                                       TaskCallback(0x001D9510), 0,
                                       TaskUserData(work), work->calc_task);
    AsdTask_CreateDraw("QuestCenterDrawUp L", 0xDB, 1, 0,
                       TaskCallback(0x001D9510), 0,
                       TaskUserData(work), work->calc_task);
    work->draw_down = AsdTask_CreateDraw("QuestCenterDrawDown", 0xE7, 1, 0,
                                         TaskCallback(0x001FE0F8), 0,
                                         TaskUserData(work), work->calc_task);
}

// ---------------------------------------------------------------------------
// eventCommand.cpp (0x0025955C), 516 B
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x0025955c, 516)
void eventCommand_func_0025955c(u32 owner, s32 frames, u32 mode, f32 alpha) {
    if (g_EventCommandWork == nullptr) {
        // 0x00259590..0x002595B8: 0x100/0x100/0/0x18/1.
        g_EventCommandWork = static_cast<EventCommandWork*>(
            AsdMem_Alloc(0x100, 0x100, 0, sizeof(EventCommandWork), 1));
        g_EventCommandWork->value = 0.0f;
        g_EventCommandWork->frames = 0;
        g_EventCommandWork->field_10 = 0;

        // 0x002595C0..0x00259644: calc task (0x002E21DC, user words
        // 0x00317EB8 and the singleton) and two draw tasks (0x002E2074).
        EventCommandWork* work = g_EventCommandWork;
        work->calc_task = AsdTask_CreateCalc(
            "EventMessUnderFade_Proc", 2, 0, 0, TaskCallback(0x002E21DC),
            0x00317EB8, TaskUserData(work));
        AsdTask_CreateDraw("EventMessUnderFade_Draw", 0x80, 0, 0,
                           TaskCallback(0x002E2074), 0,
                           TaskUserData(work), work->calc_task);
        AsdTask_CreateDraw("EventMessUnderFade_Draw", 0xDE, 0, 0,
                           TaskCallback(0x002E2074), 0,
                           TaskUserData(work), work->calc_task);
    }

    EventCommandWork* work = g_EventCommandWork;
    work->frames = static_cast<u32>(frames);                // 0x00259650
    work->field_10 = 0;                                     // 0x00259654

    if (mode != 0) {
        // 0x0025965C..0x00259680: fade towards the target over `frames`.
        work->owner = owner;
        if (frames == 0) {
            work->value = alpha;
            work->step = 0.0f;
        } else {
            work->value = 0.0f;
            work->step = alpha / static_cast<f32>(frames);
        }
        return;
    }

    if (frames == 0) {
        // 0x002596CC..0x002596D4: immediate reset.
        work->owner = owner;
        work->value = 0.0f;
        work->step = 0.0f;
        return;
    }

    // 0x00259698..0x002596BC: start a decreasing fade only when the current
    // value is zero; otherwise the value is replaced without touching owner.
    if (work->value == 0.0f) {
        work->owner = owner;
    }
    work->value = alpha;
    work->step = -(alpha / static_cast<f32>(frames));
}

// ---------------------------------------------------------------------------
// EventEffect.cpp (0x0030A4FC), 504 B
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x0030a4fc, 504)
void EventEffect_func_0030a4fc() {
    if (g_EventEffectWork == nullptr) {
        // 0x0030A518..0x0030A53C: 0x100/0x100/0/0x1C/1.
        g_EventEffectWork = static_cast<EventEffectWork*>(
            AsdMem_Alloc(0x100, 0x100, 0, sizeof(EventEffectWork), 1));
    }
    EventEffectWork* work = g_EventEffectWork;

    // 0x0030A544..0x0030A580: reset and build the BlinkFade tasks.
    work->calc_task = nullptr;
    work->draw_up_left = nullptr;
    work->draw_up_right = nullptr;
    work->field_0c = 0;
    work->field_10 = 0;
    work->field_14 = 0.0f;
    work->flag_18 = 0;

    work->calc_task = AsdTask_CreateCalc("BlinkFade Calc", 1, 0, 0,
                                         TaskCallback(0x00222428), 0, 0);
    AsdTask_CreateDraw("BlinkFade DrawUpLeft", 0x81, 0, 0,
                       TaskCallback(0x002221F0), 0,
                       TaskUserData(work), work->calc_task);
    AsdTask_CreateDraw("BlinkFade DrawUpRight", 0xDF, 0, 0,
                       TaskCallback(0x002221F0), 0,
                       TaskUserData(work), work->calc_task);

    // 0x0030A5D8..0x0030A5F4: state fields.
    work->field_10 = 0;
    work->draw_up_right = nullptr;
    work->flag_18 = 0;
    work->field_14 = 1.0f;
    work->field_0c = 0x28;

    // 0x0030A5F8..0x0030A658: two texture rows of 0x0043DF00.  The group is
    // loaded first, then the (key,row) resource pair.
    for (s32 i = 0; i < 2; ++i) {
        BlinkFadeTexture* texture = &g_BlinkFadeTextures[i];
        if (!AsdTMTexTable_IsGroupLoaded(texture->key)) {
            engine::AsdTMTexTable_func_002c5b04(texture->key, 0);
            texture->table_loaded = 1;
        }
        if (!AsdRes_IsLoaded(texture->key, texture->row)) {
            AsdRes_Request(texture->key, texture->row);
            texture->res_loaded = 1;
        }
    }
}

// ---------------------------------------------------------------------------
// clearSave.cpp (0x001E1118), 488 B
// ---------------------------------------------------------------------------

// DECOMP_FUNC(0x001e1118, 488)
void clearSave_func_001e1118(u32 arg) {
    // 0x001E1124..0x001E1158: 0x100/0x100/0/0x94/1, then zero.
    ClearSaveWork* work = static_cast<ClearSaveWork*>(
        AsdMem_AllocAlign(0x100, 0x100, 0, sizeof(ClearSaveWork), 1));
    g_ClearSaveWork = work;
    AsdMem_Zero(work, sizeof(ClearSaveWork));

    if (arg == 0) {
        work->flag_08 = 1;                                  // 0x001E1164
    }
    work = g_ClearSaveWork;

    // 0x001E116C..0x001E1180: resource 0x3C, common background, button help
    // and the shared script reset.
    CampRes_LoadEntry(0x3C);
    CommonBg_func_00289b4c();
    camp::ButtonHelp_Init();
    ScriptVm_func_00289ae8();

    // 0x001E1180..0x001E11B8: clearSave.bf/.mbm and the script process.
    work->script_bf = static_cast<u32>(reinterpret_cast<std::uintptr_t>(
        ScriptRes_Load("clear_save/clearSave.bf")));
    work->msg_mbm = static_cast<u32>(reinterpret_cast<std::uintptr_t>(
        ScriptRes_Load("clear_save/clearSave.mbm")));
    work->script_process = scrScriptProcess_func_002972f8(
        reinterpret_cast<void*>(static_cast<std::uintptr_t>(work->script_bf)),
        reinterpret_cast<void*>(static_cast<std::uintptr_t>(work->msg_mbm)));
    static_cast<ScrScriptProcess*>(work->script_process)->state = 2;
    AsdRow_LoadNow(2, 0x83);                        // 0x001E11B8

    // 0x001E11BC..0x001E11DC: the clear flag drives both fade rows.
    if (work->flag_08 != 0) {
        ClearSave_SetFade(0, 0xFF);
        ClearSave_SetFade(1, 0xFF);
    }

    // 0x001E11E0..0x001E1254: calc task (0x001B0FE0 with 0x00206B40) and
    // the left/right draw tasks (0x001E1318).
    work->calc_task = AsdTask_CreateCalc("clearSave C", 2, 0, 0,
                                         TaskCallback(0x001B0FE0),
                                         0x00206B40, TaskUserData(work));
    AsdTask_CreateDraw("clearSave L", 0x65, 0, 0,
                       TaskCallback(0x001E1318), 0,
                       TaskUserData(work), work->calc_task);
    AsdTask_CreateDraw("clearSave R", 0xCC, 0, 0,
                       TaskCallback(0x001E1318), 0,
                       TaskUserData(work), work->calc_task);
}

} // namespace smt4::script
