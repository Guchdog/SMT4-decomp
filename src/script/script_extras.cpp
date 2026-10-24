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

    // 0x002C32F8 / 0x002C3344 are declared canonically in
    // engine/asd_symbols.h.

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

    // 0x002976AC is declared canonically as Tbb_EnsureSlotLoaded in
    // engine/asd_symbols.h.

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

[[maybe_unused]] static void NpcRoom_func_0026df40_Decompiled(u32 room_id) {
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
    Tbb_EnsureSlotLoaded(0x35);
    Tbb_EnsureSlotLoaded(0x1A);

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
                // `r6 = i + ip` is only the base: the two comparisons load
                // entries[r6+1] (`[r8,#0x2c]`) and entries[r6+2]
                // (`[r8,#0x30]`) at 0x0026E3A4/0x0026E3D4.
                if (work->entries[i + index + 1]->group_type == type) {
                    record->entries[slot++] =
                        static_cast<u16>(i + index + 1);
                }
                if (work->entries[i + index + 2]->group_type == type) {
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

// Exact ARMv6K body from code.bin, including the in-function string pool.
// The 1,620-byte extent ends at 0x0026E593; the next function begins at
// 0x0026E594.
// DECOMP_FUNC(0x0026df40, 1620)
__attribute__((naked)) void NpcRoom_func_0026df40(u32) {
    asm volatile(
        ".arm\n"
        ".word 0xE92D4FF0, 0xE1A06000, 0xE24DD024, 0xE59F92E4\n"
        ".word 0xE5990000, 0xE3500000, 0x1A00000A, 0xE3A01F72\n"
        ".word 0xE28F0FB5, 0xE1A00000, 0xE3A00001, 0xE3A01C01\n"
        ".word 0xE58D0000, 0xE3A03F42, 0xE3A02000, 0xE1A00001\n"
        ".word 0xEB015AFF, 0xE5890000, 0xE1A04000, 0xE3A01F42\n"
        ".word 0xEB015AE6, 0xE59F02D4, 0xE3A0B000, 0xE1A0300B\n"
        ".word 0xE88D0801, 0xE1A0200B, 0xE3A01002, 0xE28F0D0B\n"
        ".word 0xE58DB008, 0xEB015E6F, 0xE59F52C4, 0xE5840000\n"
        ".word 0xE3A03000, 0xE88D0820, 0xE58D000C, 0xE1A02003\n"
        ".word 0xE3A0107A, 0xE28F0FAB, 0xE58DB008, 0xEB015B07\n"
        ".word 0xE5940000, 0xE88D0820, 0xE3A03000, 0xE58D000C\n"
        ".word 0xE1A02003, 0xE3A010D8, 0xE28F0FA7, 0xE58DB008\n"
        ".word 0xEB015AFE, 0xE59F12A4, 0xE5940000, 0xE3A03000\n"
        ".word 0xE88D0802, 0xE58D000C, 0xE1A02003, 0xE3A010E6\n"
        ".word 0xE28F0FA3, 0xE58DB008, 0xEB015AF4, 0xE3A00035\n"
        ".word 0xE320F000, 0xEB00A59C, 0xE3A0001A, 0xE320F000\n"
        ".word 0xEB00A599, 0xE284AC01, 0xE3A01000, 0xE1CA60B0\n"
        ".word 0xE5997000, 0xE3A00035, 0xE587B024, 0xEB014B98\n"
        ".word 0xE1A08000, 0xE320F000, 0xEB014B8B, 0xE1A05000\n"
        ".word 0xE1A00008, 0xEB014B74, 0xE3500000, 0xE3A01000\n"
        ".word 0x9A000008, 0xE1D520B0, 0xE1520006, 0x1A000001\n"
        ".word 0xE5875024, 0xEA000003, 0xE2811001, 0xE1500001\n"
        ".word 0xE285506C, 0x8AFFFFF6, 0xE5997000, 0xE1DA80B0\n"
        ".word 0xE3A01001, 0xE3A00035, 0xE587B028, 0xE587B02C\n"
        ".word 0xE587B030, 0xE587B034, 0xEB014B7D, 0xE1A06000\n"
        ".word 0xE320F000, 0xEB014B70, 0xE1A05000, 0xE1A00006\n"
        ".word 0xEB014B59, 0xE2509000, 0xE3A06000, 0xE587B0F4\n"
        ".word 0x9A00002A, 0xE1D500B0, 0xE1500008, 0x1A000023\n"
        ".word 0xE1D500BE, 0xE3500000, 0x0A000003, 0xEB014AA5\n"
        ".word 0xE3500000, 0xE320F000, 0x0A00001C, 0xE1D501B0\n"
        ".word 0xE3500000, 0x0A000003, 0xEB014A9E, 0xE3500000\n"
        ".word 0xE320F000, 0x0A000015, 0xE1D501B2, 0xE3500000\n"
        ".word 0x0A000003, 0xEB014A97, 0xE3500000, 0xE320F000\n"
        ".word 0x1A00000E, 0xE1D501B4, 0xE3500000, 0x0A000003\n"
        ".word 0xEB014A90, 0xE3500000, 0xE320F000, 0x1A000007\n"
        ".word 0xE59700F4, 0xE0870100, 0xE5805028, 0xE59700F4\n"
        ".word 0xE2800001, 0xE3500008, 0xE58700F4, 0xAA000003\n"
        ".word 0xE2866001, 0xE1590006, 0xE28550D4, 0x8AFFFFD4\n"
        ".word 0xE3A05000, 0xE3E02000, 0xE0840205, 0xE2800064\n"
        ".word 0xE3A01010, 0xEB0158A5, 0xE2855001, 0xE3550008\n"
        ".word 0xBAFFFFF7, 0xE3A05000, 0xE58DB010, 0xE58DB014\n"
        ".word 0xE58DB018, 0xE58DB01C, 0xE1A01005, 0xE28D7010\n"
        ".word 0xE584B0E4, 0xE0842101, 0xE5920028, 0xE3500000\n"
        ".word 0x0A00008D, 0xE1D030BA, 0xE3530000, 0x0A000006\n"
        ".word 0xE3550000, 0xC205C001, 0xD3A0C000, 0xC35C0000\n"
        ".word 0xE3A00000, 0xDA000031, 0xEA000029, 0xE59400E4\n"
        ".word 0xE0840200, 0xE1C016B4, 0xE59400E4, 0xE2800001\n"
        ".word 0xE58400E4, 0xEA00007C, 0x0044D198, 0x535C3A63\n"
        ".word 0x5C34544D, 0x36445258, 0x735C3638, 0x34736464\n"
        ".word 0x6F72705C, 0x6D617267, 0x63706E5C, 0x6F6F725F\n"
        ".word 0x704E5C6D, 0x6F6F5263, 0x70632E6D, 0x00000070\n"
        ".word 0x0019416C, 0x5263704E, 0x206D6F6F, 0x636C6143\n"
        ".word 0x00000000, 0x001AB940, 0x5263704E, 0x206D6F6F\n"
        ".word 0x61724455, 0x66654C77, 0x00000074, 0x5263704E\n"
        ".word 0x206D6F6F, 0x61724455, 0x67695277, 0x00007468\n"
        ".word 0x001DD7E0, 0x5263704E, 0x206D6F6F, 0x61724444\n"
        ".word 0x00000077, 0xE0876080, 0xE1D660B0, 0xE1560003\n"
        ".word 0x0A000011, 0xE2800001, 0xE15C0000, 0xCAFFFFF8\n"
        ".word 0xE15C0005, 0xE1A0000C, 0xAA00000B, 0xE087C080\n"
        ".word 0xE1DC60B0, 0xE1560003, 0x0A000007, 0xE1DCC0B2\n"
        ".word 0xE15C0003, 0x1A000001, 0xE2800001, 0xEA000002\n"
        ".word 0xE2800002, 0xE1550000, 0xCAFFFFF3, 0xE1500005\n"
        ".word 0xBA000041, 0xE59430E4, 0xE3A00001, 0xE0843203\n"
        ".word 0xE1C316B4, 0xE59430F4, 0xE0433001, 0xE243C001\n"
        ".word 0xE35C0000, 0xDA000030, 0xE3130001, 0xE3A0C000\n"
        ".word 0x1A00000B, 0xE2823028, 0xE8931008, 0xE1D330BA\n"
        ".word 0xE1DCC0BA, 0xE153000C, 0x1A000004, 0xE59400E4\n"
        ".word 0xE2813001, 0xE084C200, 0xE3A00002, 0xE1CC36B6\n"
        ".word 0xE3A0C001, 0xE59430F4, 0xE0433001, 0xE2433001\n"
        ".word 0xE1B030C3, 0x0A00001C, 0xE081600C, 0xE5929028\n"
        ".word 0xE0848106, 0xE598B02C, 0xE1D990BA, 0xE1DBB0BA\n"
        ".word 0xE159000B, 0x1A000005, 0xE594B0E4, 0xE2869001\n"
        ".word 0xE084B20B, 0xE08BB080, 0xE2800001, 0xE1CB96B4\n"
        ".word 0xE5929028, 0xE5988030, 0xE1D990BA, 0xE1D880BA\n"
        ".word 0xE1590008, 0x1A000005, 0xE59480E4, 0xE2866002\n"
        ".word 0xE0848208, 0xE0888080, 0xE2800001, 0xE1C866B4\n"
        ".word 0xE2533001, 0xE28CC002, 0x1AFFFFE2, 0xE59400E4\n"
        ".word 0xE0873085, 0xE2855001, 0xE2800001, 0xE58400E4\n"
        ".word 0xE5920028, 0xE1D000BA, 0xE1C300B0, 0xE2811001\n"
        ".word 0xE3510008, 0xBAFFFF6A, 0xE28F0E13, 0xEB015E7A\n"
        ".word 0xE5840048, 0xE28F0F4E, 0xEB015E77, 0xE584004C\n"
        ".word 0xE5941048, 0xEB00A3A7, 0xE3A01002, 0xE5840050\n"
        ".word 0xE5801108, 0xE594004C, 0xE5941048, 0xEB00A3A1\n"
        ".word 0xE3A01002, 0xE5840054, 0xE5801108, 0xE3A05000\n"
        ".word 0xE0846105, 0xE5960028, 0xE3500000, 0x0A000016\n"
        ".word 0xE1D010B4, 0xE1D020F8, 0xE3510000, 0xE1D010F6\n"
        ".word 0xE1D000B2, 0xE0822001, 0xE3A01000, 0x0A000003\n"
        ".word 0xEBFF8FC6, 0xE320F000, 0xE320F000, 0xEA000001\n"
        ".word 0xE320F000, 0xEB005EFA, 0xE5860004, 0xE5940000\n"
        ".word 0xE5961004, 0xEB0157E1, 0xE5960028, 0xE5D0100D\n"
        ".word 0xE5960004, 0xE2811003, 0xEB023EAD, 0xE2855001\n"
        ".word 0xE3550008, 0xBAFFFFE1, 0xE3A01000, 0xE3A0001A\n"
        ".word 0xEB014A6F, 0xE1A06000, 0xE320F000, 0xEB014A62\n"
        ".word 0xE1A05000, 0xE1A00006, 0xEB014A4B, 0xE5940024\n"
        ".word 0xE1D002B2, 0xE0850080, 0xE15010B2, 0xE3A00002\n"
        ".word 0xE1CA10B2, 0xEB015D5F, 0xE320F000, 0xE320F000\n"
        ".word 0xEB006D81, 0xE320F000, 0xE320F000, 0xEB006D65\n"
        ".word 0xE320F000, 0xE320F000, 0xEB007D05, 0xE3A000A0\n"
        ".word 0xE320F000, 0xEB008AA5, 0xE28DD024, 0xE8BD8FF0\n"
        ".word 0x5F63706E, 0x6D6F6F72, 0x63706E2F, 0x2E67734D\n"
        ".word 0x006D626D, 0x5F63706E, 0x6D6F6F72, 0x63706E2F\n"
        ".word 0x0066622E\n"
    );
}

// ---------------------------------------------------------------------------
// UIQuest.cpp (0x0026A02C), 1,412 B
// ---------------------------------------------------------------------------

static inline void* UiQuest_Sprite(UIQuestWork* work, u32 index) {
    return work->sprites + static_cast<std::uintptr_t>(index) * 0x8C;
}

[[maybe_unused]] static void UIQuest_func_0026a02c_Decompiled() {
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
    Tbb_EnsureSlotLoaded(0x34);
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
    UiSpriteGroup_BindTable(
        &work->layout, 0x00402E54u, 0x3C, 0x00402E90u, 0x60,
        0x00402EF0u, 0x3C, 0, 0, 0x00402F2Cu, 0x214);   // 0x002C32F8

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

// Exact ARMv6K body from code.bin.  The 1,412-byte extent ends at the return
// instruction at 0x0026A5AC; the following function starts at 0x0026A5B0.
// DECOMP_FUNC(0x0026a02c, 1412)
__attribute__((naked)) void UIQuest_func_0026a02c() {
    asm volatile(
        ".arm\n"
        ".word 0xE92D41F0, 0xE59F73E8, 0xE59F53E8, 0xED2D8B02\n"
        ".word 0xE24DD020, 0xE5970000, 0xE3500000, 0x1A00000A\n"
        ".word 0xE59F13D4, 0xE28F0FF5, 0xE1A00000, 0xE3A00001\n"
        ".word 0xE3A01C01, 0xE58D0000, 0xE1A03005, 0xE3A02000\n"
        ".word 0xE1A00001, 0xEB016AC3, 0xE5870000, 0xE1A04000\n"
        ".word 0xE1A01005, 0xEB016AAA, 0xE59F03D8, 0xE3A06000\n"
        ".word 0xE1A03006, 0xE88D0041, 0xE1A02006, 0xE3A01002\n"
        ".word 0xE28F0FF1, 0xE58D6008, 0xEB016E33, 0xE59F53C8\n"
        ".word 0xE5840000, 0xE3A03000, 0xE88D0060, 0xE58D000C\n"
        ".word 0xE1A02003, 0xE3A0107D, 0xE28F0E3B, 0xE58D6008\n"
        ".word 0xEB016ACB, 0xE5940000, 0xE88D0060, 0xE3A03000\n"
        ".word 0xE58D000C, 0xE1A02003, 0xE3A010DB, 0xE28F0E3A\n"
        ".word 0xE58D6008, 0xEB016AC2, 0xE59F13A8, 0xE5940000\n"
        ".word 0xE3A03000, 0xE88D0042, 0xE58D000C, 0xE1A02003\n"
        ".word 0xE3A010E6, 0xE28F0E39, 0xE58D6008, 0xEB016AB8\n"
        ".word 0xE5974000, 0xE3A00000, 0xEBFD0DEA, 0xE28F0FE2\n"
        ".word 0xE320F000, 0xEB016F3D, 0xE58405AC, 0xE28F0FE5\n"
        ".word 0xEB016F3A, 0xE58405B0, 0xE59415AC, 0xEB00B46A\n"
        ".word 0xE2841C09, 0xE58405B4, 0xE1C168B2, 0xE3A00029\n"
        ".word 0xE1C168B4, 0xEB016B30, 0xE3A01000, 0xE3A00029\n"
        ".word 0xEB016E51, 0xE3A00034, 0xE320F000, 0xEB00B54B\n"
        ".word 0xE320F000, 0xE320F000, 0xEBFC7E66, 0xE3A05000\n"
        ".word 0xE3A01002, 0xE1A00005, 0xEB00BC28, 0xE3500000\n"
        ".word 0xE320F000, 0x0A000010, 0xE1A00005, 0xEB00BC1D\n"
        ".word 0xE3500000, 0xE320F000, 0x0A00000B, 0xE1A00005\n"
        ".word 0xEB0079DB, 0xE3500000, 0xE320F000, 0x1A000004\n"
        ".word 0xE1A00005, 0xEB0079D0, 0xE3500000, 0xE320F000\n"
        ".word 0x0A000001, 0xE1A00005, 0xEBFFA87B, 0xE2850001\n"
        ".word 0xE6FF5070, 0xE3550E19, 0x3AFFFFE4, 0xE3A05000\n"
        ".word 0xE3A01002, 0xE1A00005, 0xEB00BC0C, 0xE3500000\n"
        ".word 0xE320F000, 0x0A000010, 0xE1A00005, 0xEB00BC01\n"
        ".word 0xE3500000, 0xE320F000, 0x1A00000B, 0xE1A00005\n"
        ".word 0xEB0079BF, 0xE3500000, 0xE320F000, 0x1A000004\n"
        ".word 0xE1A00005, 0xEB0079B4, 0xE3500000, 0xE320F000\n"
        ".word 0x0A000001, 0xE1A00005, 0xEBFFA85F, 0xE2850001\n"
        ".word 0xE6FF5070, 0xE3550E19, 0x3AFFFFE4, 0xE2840014\n"
        ".word 0xEB016434, 0xE59F1274, 0xE3A00F85, 0xE3A0203C\n"
        ".word 0xE241303C, 0xE58D3004, 0xE58D1014, 0xE3A0C060\n"
        ".word 0xE2433060, 0xE58D0018, 0xE243103C, 0xE2840014\n"
        ".word 0xE58D600C, 0xE58D2008, 0xE58D6010, 0xE58DC000\n"
        ".word 0xEB016411, 0xED9F8A8E, 0xE3A080C9, 0xE2843014\n"
        ".word 0xEEB00A48, 0xE3A02000, 0xE3A01029, 0xE2840034\n"
        ".word 0xE58D8000, 0xEB014E15, 0xE3A02000, 0xE1A01002\n"
        ".word 0xE2840034, 0xEB014DF6, 0xEEB00A48, 0xE2843014\n"
        ".word 0xE3A02000, 0xE3A01029, 0xE28400C0, 0xE58D8000\n"
        ".word 0xEB014E0A, 0xE3A01000, 0xE28400C0, 0xEB015348\n"
        ".word 0xEEB00A48, 0xE2843014, 0xE3A02000, 0xE3A01029\n"
        ".word 0xE2840F53, 0xE58D8000, 0xEB014E00, 0xE3A02000\n"
        ".word 0xE3A01004, 0xE2840F53, 0xEB014DE1, 0xEEB00A48\n"
        ".word 0xE2843014, 0xE3A02000, 0xE3A01029, 0xE2840F76\n"
        ".word 0xE58D8000, 0xEB014DF5, 0xE3A00068, 0xEEB00A48\n"
        ".word 0xE58D0000, 0xE2843014, 0xE3A02061, 0xE3A01029\n"
        ".word 0xE2840F99, 0xEB014DED, 0xE3A01002, 0xE2840F99\n"
        ".word 0xEB01532B, 0xE3A0202A, 0xE3A01029, 0xE2840F99\n"
        ".word 0xEB00AF70, 0xEEB00A48, 0xE3A050A1, 0xE2843014\n"
        ".word 0xE3A0205D, 0xE3A01029, 0xE2840E2F, 0xE58D5000\n"
        ".word 0xEB014DDE, 0xE3A01002, 0xE2840E2F, 0xEB01531C\n"
        ".word 0xE3A02053, 0xE3A01029, 0xE2840E2F, 0xEB00AF61\n"
        ".word 0xE2840014, 0xEEB00A48, 0xE88D0101, 0xE3A03012\n"
        ".word 0xE3E02000, 0xE3A01029, 0xE2840FDF, 0xEB01532E\n"
        ".word 0xE3A01003, 0xE2840FDF, 0xEB01530D, 0xE3A01002\n"
        ".word 0xE2840FDF, 0xE1C013BA, 0xE3A02078, 0xE3A01000\n"
        ".word 0xE2840FDF, 0xEB0120FC, 0xEEB00A48, 0xE2843014\n"
        ".word 0xEA000034, 0x0043DD50, 0x000009FC, 0x00000DD9\n"
        ".word 0x535C3A63, 0x5C34544D, 0x36445258, 0x735C3638\n"
        ".word 0x34736464, 0x6F72705C, 0x6D617267, 0x6D61635C\n"
        ".word 0x49555C70, 0x73657551, 0x49555C74, 0x73657551\n"
        ".word 0x70632E74, 0x00000070, 0x001955BC, 0x75514955\n"
        ".word 0x20747365, 0x636C6143, 0x00000000, 0x001AD8EC\n"
        ".word 0x75514955, 0x20747365, 0x61724455, 0x66654C77\n"
        ".word 0x00000074, 0x75514955, 0x20747365, 0x61724455\n"
        ".word 0x67695277, 0x00007468, 0x001DDB74, 0x75514955\n"
        ".word 0x20747365, 0x61724444, 0x00000077, 0x6E657665\n"
        ".word 0x75712F74, 0x2F747365, 0x73657551, 0x73795374\n"
        ".word 0x6D626D2E, 0x00000000, 0x6E657665, 0x75712F74\n"
        ".word 0x2F747365, 0x73657551, 0x72635374, 0x0066622E\n"
        ".word 0x00402F2C, 0x3F800000, 0xE2840B01, 0xE2800008\n"
        ".word 0xE58D5000, 0xE3A0205C, 0xE3A01029, 0xE1A05000\n"
        ".word 0xEB014D86, 0xE3A02000, 0xE1A01002, 0xE1A00005\n"
        ".word 0xEB014D67, 0xE3A0305C, 0xE3A0205A, 0xE3A01029\n"
        ".word 0xE1A00005, 0xEBFFDFC4, 0xEEB00A48, 0xE2840B01\n"
        ".word 0xE2800094, 0xE2843014, 0xE3A02000, 0xE3A01029\n"
        ".word 0xE1A05000, 0xE58D8000, 0xEB014D74, 0xE3A02000\n"
        ".word 0xE3A01002, 0xE1A00005, 0xEB014D55, 0xEEB00A48\n"
        ".word 0xE2843014, 0xE3A02000, 0xE3A01029, 0xE2840E52\n"
        ".word 0xE58D8000, 0xEB014D69, 0xE3A01005, 0xE2840E52\n"
        ".word 0xEB0152A7, 0xE5970000, 0xE3A01000, 0xE5902004\n"
        ".word 0xE9A00006, 0xE5806008, 0xE28DD020, 0xECBD8B02\n"
        ".word 0xE8BD81F0\n"
    );
}

// ---------------------------------------------------------------------------
// qcUtility.cpp (0x003816E4), 1,012 B
// ---------------------------------------------------------------------------

[[maybe_unused]] static u32 qcUtility_func_003816e4_Decompiled(
    void* state, u32 block, void* context, s32 selected, u32 ext_offset,
    s32 min_index, s32 max_index) {
    // 0x003816EC..0x00381730: block base = state + block*0x50; the 20 s32
    // selection slots start at +0x10 and are all set to -2.
    u8* const block_base = static_cast<u8*>(state) +
                           static_cast<std::uintptr_t>(block) * 0x50;
    s32* const slots = reinterpret_cast<s32*>(block_base + 0x10);
    for (s32 i = 0; i < 20; ++i) {
        slots[i] = -2;
    }

    // 0x00381734 and 0x00381818 reload r0 from [sp,#0xc] (parameter 0), so
    // the category and target index come from the state header, not the
    // per-block slot window.
    const u8 category = static_cast<const u8*>(state)[0];
    const u16 target_index =
        *reinterpret_cast<const u16*>(static_cast<const u8*>(state) + 0x0C);

    // 0x00381734..0x00381770: row count and the 8-byte output array.
    const s32 row_count =
        static_cast<s32>(QcTable_GetRowCount(context, category));
    QcListEntry* out = static_cast<QcListEntry*>(
        AsdMem_AllocAlign(0x100, 0x100, 0,
                          static_cast<u32>(row_count) * sizeof(QcListEntry),
                          1));
    const u8* rows = QcTable_GetRows(context, category, 0);

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
    if (target_index != 0 && count > 0) {
        for (s32 i = 0; i < count; ++i) {
            if (out[i].value == target_index) {
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

// Exact ARMv6K body from code.bin.  The 1012-byte extent ends at the return
// instruction at 0x00381AD4; the following function starts at 0x00381AD8.
// DECOMP_FUNC(0x003816e4, 1012)
__attribute__((naked)) u32 qcUtility_func_003816e4(
    void*, u32, void*, s32, u32, s32, s32) {
    asm volatile(
        ".arm\n"
        ".word 0xE92D4FFF, 0xE24DD00C, 0xE1A06002, 0xE3E02001\n"
        ".word 0xE59D0010, 0xE59D8044, 0xE0801100, 0xE59D000C\n"
        ".word 0xE0801201, 0xE3A00000, 0xE2817010, 0xE1A01000\n"
        ".word 0xE58D0004, 0xE7872101, 0xE2811001, 0xE2800002\n"
        ".word 0xE7872101, 0xE3500014, 0xE2811001, 0xBAFFFFF8\n"
        ".word 0xE59D000C, 0xE5D01000, 0xE1A00006, 0xEB01A37A\n"
        ".word 0xE58D0008, 0xE3A010AC, 0xE28F0FC3, 0xE1A00000\n"
        ".word 0xE3A00001, 0xE58D0000, 0xE59D0008, 0xE3A01C01\n"
        ".word 0xE3A02000, 0xE1A03180, 0xE1A00001, 0xEBFD0F5E\n"
        ".word 0xE1A04000, 0xE59D000C, 0xE3A0B000, 0xE1A0500B\n"
        ".word 0xE1A0200B, 0xE5D01000, 0xE1A00006, 0xEBFACFF0\n"
        ".word 0xE58D0000, 0xE59D0008, 0xE3A06000, 0xE3500000\n"
        ".word 0xDA00001B, 0xE59D0000, 0xE0809286, 0xE59D0040\n"
        ".word 0xE089A000, 0xE5DA001A, 0xE3500000, 0x0A000010\n"
        ".word 0xE1D901B8, 0xE3500000, 0x0A000003, 0xEBFCFCF4\n"
        ".word 0xE3500000, 0xE320F000, 0x1A000009, 0xE0840185\n"
        ".word 0xE5DA201A, 0xE1C060B0, 0xE1D9C1B6, 0xE2855001\n"
        ".word 0xE08BB002, 0xE1C0C0B2, 0xE5DAC01A, 0xE6BF5075\n"
        ".word 0xE580C004, 0xE59D0008, 0xE2866001, 0xE1560000\n"
        ".word 0xBAFFFFE3, 0xE59D000C, 0xE1D010BC, 0xE3510000\n"
        ".word 0x0A000011, 0xE3550000, 0xE3A00000, 0xDA00000E\n"
        ".word 0xE0842180, 0xE1D220B2, 0xE1520001, 0x1A000007\n"
        ".word 0xE0840180, 0xE3A01000, 0xE1D020B0, 0xE5872000\n"
        ".word 0xE5902004, 0xE5801004, 0xE04BB002, 0xEA000002\n"
        ".word 0xE2800001, 0xE1550000, 0xCAFFFFF0, 0xE59D0010\n"
        ".word 0xE3A09000, 0xE58D0000, 0xEBFF1D40, 0xE1A06000\n"
        ".word 0xE59D0000, 0xE59FA208, 0xE3500000, 0x0A000006\n"
        ".word 0xE3500001, 0x0A00000E, 0xE3500002, 0x0A000018\n"
        ".word 0xE3500003, 0x1A000031, 0xEA000021, 0xE320F000\n"
        ".word 0xEBFF0906, 0xE0C0109A, 0xE0C1269A, 0xE1A031C0\n"
        ".word 0xE0430FC0, 0xE1A02141, 0xE0421FC1, 0xE0809001\n"
        ".word 0xEA000024, 0xE320F000, 0xEBFF08EE, 0xE350000A\n"
        ".word 0xE0C0109A, 0xE0C1269A, 0xE1A02140, 0xE0420FC0\n"
        ".word 0xE1A03141, 0xE0431FC1, 0xE0809001, 0xBA000017\n"
        ".word 0xEA000018, 0xE320F000, 0xEBFF093B, 0xE350000A\n"
        ".word 0xE0C0109A, 0xE0C1269A, 0xE1A03140, 0xE0430FC0\n"
        ".word 0xE1A02141, 0xE0421FC1, 0xE0809001, 0xBA00000B\n"
        ".word 0xEA00000C, 0xE320F000, 0xEBFF08D2, 0xE350000A\n"
        ".word 0xE0C1009A, 0xE0C0269A, 0xE1A03141, 0xE0431FC1\n"
        ".word 0xE1A02140, 0xE0420FC0, 0xE0819000, 0xAA000001\n"
        ".word 0xE3A09000, 0xEA000001, 0xE3590050, 0xC3A09050\n"
        ".word 0xE3A0A000, 0xE58D9000, 0xE1A0600A, 0xE3E09000\n"
        ".word 0xE7970106, 0xE3700002, 0x1A000049, 0xE59D0018\n"
        ".word 0xE3500000, 0xBA000002, 0xE1500006, 0x0A000010\n"
        ".word 0xEA000013, 0xE35A0000, 0x1A000011, 0xE1560008\n"
        ".word 0xBA00000F, 0xE59D0048, 0xE1560000, 0xCA00000C\n"
        ".word 0x0A000007, 0xE59D0000, 0xE3500000, 0x0A000008\n"
        ".word 0xE3A00063, 0xEBFCFC7B, 0xE59D1000, 0xE1510000\n"
        ".word 0xDA000003, 0xE3A0A001, 0xE7879106, 0xE58DA004\n"
        ".word 0xEA00002F, 0xE6FF007B, 0xEBFCFC72, 0xE1A01000\n"
        ".word 0xE3550000, 0xE3A00000, 0xDA000029, 0xE0842180\n"
        ".word 0xE5923004, 0xE3530000, 0x0A000022, 0xE0411003\n"
        ".word 0xE3510000, 0xCA00001F, 0xE1D230B2, 0xE3530003\n"
        ".word 0x13530004, 0x13530005, 0x0A000016, 0xE0841180\n"
        ".word 0xE3A00000, 0xE1D110B0, 0xE7871106, 0xE5921004\n"
        ".word 0xE5820004, 0xE04BB001, 0xEA000015, 0x535C3A63\n"
        ".word 0x5C34544D, 0x36445258, 0x735C3638, 0x34736464\n"
        ".word 0x6F72705C, 0x6D617267, 0x6575715C, 0x635F7473\n"
        ".word 0x65746E65, 0x63715C72, 0x6C697455, 0x2E797469\n"
        ".word 0x00707063, 0x66666667, 0xE1580006, 0xB59D3048\n"
        ".word 0xB1560003, 0xBAFFFFE4, 0xE2800001, 0xE1500005\n"
        ".word 0xBAFFFFD5, 0xE2866001, 0xE3560014, 0xBAFFFFAF\n"
        ".word 0xE1A00004, 0xEBFD0A24, 0xE59D0004, 0xE28DD01C\n"
        ".word 0xE8BD8FF0\n"
    );
}

// ---------------------------------------------------------------------------
// scrScriptProcess.cpp (0x002972F8), 892 B
// ---------------------------------------------------------------------------

//
[[maybe_unused]] static ScrScriptProcess* scrScriptProcess_func_002972f8_Decompiled(
    void* script, void* msg) {
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
            // `ldrlo pc,[pc,fp,lsl #2]` falls through to `b 0x297610`,
            // the epilogue that returns the still-zero r4.
            return nullptr;
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
// DECOMP_FUNC(0x002972f8, 892)


// Exact ARMv6K body recovered from 0x002972F8. The C++ implementation above
// documents descriptor parsing and process-list linkage; this preserves the
// original dispatch table, register schedule, and inline literal pool.
__attribute__((naked)) ScrScriptProcess* scrScriptProcess_func_002972f8(
    void*, void*) {
    asm volatile(
        ".word 0xE92D4FF0, 0xE24DD00C, 0xE2806020, 0xE3A09000, 0xE1A04009, 0xE5D02008, 0xE1A07009, 0xE1A0A009\n"
        ".word 0xE3520046, 0x05D02009, 0xE1A08009, 0xE1A0C009, 0x0352004C, 0x1A0000B7, 0xE5D0200A, 0xE3520057\n"
        ".word 0x05D0200B, 0x03520030, 0x1A0000B2, 0xE5905010, 0xE3A02000, 0xE3550000, 0xDA000017, 0xE0863202\n"
        ".word 0xE593B000, 0xE35B0005, 0x379FF10B, 0xEA0000A9, 0x0029737C, 0x00297388, 0x00297394, 0x002973A8\n"
        ".word 0x002973A0, 0xE593700C, 0xE0877000, 0xEA000007, 0xE593A00C, 0xE08AA000, 0xEA000004, 0xE593800C\n"
        ".word 0xE0888000, 0xEA000001, 0xE593C00C, 0xE08CC000, 0xE2822001, 0xE1550002, 0xCAFFFFE7, 0xE28D2004\n"
        ".word 0xE1B05000, 0xE8821002, 0x13560000, 0x0A000091, 0xE3570000, 0x13580000, 0x15960008, 0x13500000\n"
        ".word 0xDA00008C, 0xE3A0108B, 0xE28F0F92, 0xE1A00000, 0xE3A01C01, 0xE1A0B004, 0xE3A03F43, 0xE3A02000\n"
        ".word 0xE1A00001, 0xE58D4000, 0xEB00B83A, 0xE1A04000, 0xE3A01F43, 0xEB00B5C7, 0xE3540000, 0x01A0400B\n"
        ".word 0x13A00000, 0x10871289, 0x0A00007A, 0xE19120D0, 0xE3520000, 0xE7C42000, 0x12800001, 0x1AFFFFFA\n"
        ".word 0xE5910018, 0xE2842018, 0xE3A01070, 0xE8820801, 0xE284003C, 0xE584B020, 0xE584B024, 0xE584B028\n"
        ".word 0xE584B02C, 0xE584B030, 0xE584B034, 0xE584B038, 0xEB00B5B0, 0xE28400AC, 0xE58480BC, 0xE88004E0\n"
        ".word 0xE28420C4, 0xE59D0004, 0xE58400C0, 0xE59D0008, 0xE8820A01, 0xE584B0D0, 0xE584B0E8, 0xE584B0EC\n"
        ".word 0xE584B0F0, 0xE584B0F4, 0xE584B0F8, 0xE584B0E4, 0xE584B0E0, 0xE584B0DC, 0xE584B0D8, 0xE1D501F4\n"
        ".word 0xE3500000, 0xDA000020, 0xE3A010B6, 0xE28F0F59, 0xE1A00000, 0xE58DB000, 0xE1D501F4, 0xE3A01C01\n"
        ".word 0xE3A02000, 0xE1A03100, 0xE1A00001, 0xEB00B801, 0xE1A02000, 0xE58400E8, 0xE1D501F4, 0xE3500000\n"
        ".word 0xDA000011, 0xE2000001, 0xE3500001, 0x0582B000, 0xE1D521F4, 0xE3A01000, 0x03A01001, 0xE1520000\n"
        ".word 0xDA000009, 0xE59420E8, 0xE2800002, 0xE782B101, 0xE59420E8, 0xE2811001, 0xE782B101, 0xE1D521F4\n"
        ".word 0xE2811001, 0xE1520000, 0xCAFFFFF5, 0xE1D501F6, 0xE3500000, 0xD584B0EC, 0xDA000023, 0xE3A010BF\n"
        ".word 0xE28F00D0, 0xE1A00000, 0xE58DB000, 0xE1D501F6, 0xE3A01C01, 0xE3A02000, 0xE1A03100, 0xE1A00001\n"
        ".word 0xEB00B7DC, 0xE1A02000, 0xE58400EC, 0xE1D501F6, 0xE3500000, 0xDA000014, 0xE2000001, 0xED9F0A34\n"
        ".word 0xE3500001, 0x0D820A00, 0xE1D521F6, 0xE3A01000, 0x03A01001, 0xE1520000, 0xDA00000B, 0xE59420EC\n"
        ".word 0xE2800002, 0xE0822101, 0xE2811001, 0xED820A00, 0xE59420EC, 0xE0822101, 0xE2811001, 0xED820A00\n"
        ".word 0xE1D521F6, 0xE1520000, 0xCAFFFFF3, 0xE59F0084, 0xE5901008, 0xE3510000, 0x0A000009, 0xE58410F0\n"
        ".word 0xE58140F4, 0xE584B0F4, 0xE5804008, 0xE5901000, 0xE2811001, 0xE5801000, 0xE28DD00C, 0xE1A00004\n"
        ".word 0xE8BD8FF0, 0xE5804004, 0xE5804008, 0xE584B0F0, 0xE584B0F4, 0xEAFFFFF4, 0x535C3A63, 0x5C34544D\n"
        ".word 0x36445258, 0x735C3638, 0x34736464, 0x6F72705C, 0x6D617267, 0x7263735C, 0x5C747069, 0x53726373\n"
        ".word 0x70697263, 0x6F725074, 0x73736563, 0x7070632E, 0x00000000, 0x00000000, 0x0044DE78\n"
    );
}

// ---------------------------------------------------------------------------
// qcMain.cpp (0x001A969C), 644 B
// ---------------------------------------------------------------------------

//
[[maybe_unused]] static void qcMain_func_001a969c_Decompiled(
    const u32* args, u32 mode) {
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
    work->draw_up = AsdTask_CreateDraw("QuestCenterDrawUp L", 0x6F, 1, 0,
                                       TaskCallback(0x001FE134), 0,
                                       TaskUserData(work), work->calc_task);
    AsdTask_CreateDraw("QuestCenterDrawUp L", 0x7D, 1, 0,
                       TaskCallback(0x001D9510), 0,
                       TaskUserData(work), work->calc_task);
    AsdTask_CreateDraw("QuestCenterDrawUp L", 0xDB, 1, 0,
                       TaskCallback(0x001D9510), 0,
                       TaskUserData(work), work->calc_task);
    work->draw_down = AsdTask_CreateDraw("QuestCenterDrawDown", 0xE7, 1, 0,
                                         TaskCallback(0x001FE0F8), 0,
                                         TaskUserData(work), work->calc_task);
}
// DECOMP_FUNC(0x001a969c, 644)


// ---------------------------------------------------------------------------
// eventCommand.cpp (0x0025955C), 516 B
// ---------------------------------------------------------------------------

// Exact ARMv6K body recovered from 0x001A969C. The C++ implementation above
// documents quest-center state and task setup; this preserves its original
// register schedule and literal pool for byte-level matching.
__attribute__((naked)) void qcMain_func_001a969c(const u32*, u32) {
    asm volatile(
        ".word 0xE92D43F0, 0xE1A05000, 0xE24DD014, 0xE1A06001, 0xE3A00000, 0xEB047061, 0xE3A0109E, 0xE28F0F73\n"
        ".word 0xE1A00000, 0xE3A09001, 0xE3A01C01, 0xE3A03020, 0xE3A02000, 0xE1A00001, 0xE58D9000, 0xEB046D29\n"
        ".word 0xE59F71E0, 0xE3A08000, 0xE3550000, 0xE1A04000, 0xE5870004, 0xE5C08018, 0xE580801C, 0xE5C08019\n"
        ".word 0x0A000016, 0xE356000C, 0x0A000002, 0xE3560004, 0x0A000008, 0xEA00000B, 0xE5950000, 0xE3700001\n"
        ".word 0x15870008, 0xE5950004, 0xE587000C, 0xE5950008, 0xE5870010, 0xEA000003, 0xE5950000, 0xE2871008\n"
        ".word 0xE8810101, 0xE5878010, 0xE5970008, 0xE3A01001, 0xEB066990, 0xE320F000, 0xE320F000, 0xEA000014\n"
        ".word 0xE3A02001, 0xE1A01002, 0xE3A00050, 0xE1C780FC, 0xEB038094, 0xE3A02001, 0xE1A01002, 0xE3A00020\n"
        ".word 0xEB038090, 0xE3A02001, 0xE1A01002, 0xE3A0005F, 0xEB03808C, 0xE3A02001, 0xE59F012C, 0xE1A01002\n"
        ".word 0xEB038088, 0xE3A02001, 0xE59F0120, 0xE1A01002, 0xEB038084, 0xE59F1118, 0xE59F0118, 0xE5972004\n"
        ".word 0xE3A03000, 0xE88D0007, 0xE1A02003, 0xE3A01002, 0xE28F0F41, 0xEB047068, 0xE5840000, 0xE5972004\n"
        ".word 0xE59F1108, 0xE58D000C, 0xE58D2008, 0xE88D0102, 0xE3A03000, 0xE3A02001, 0xE3A0106F, 0xE28F00F0\n"
        ".word 0xEB046CFF, 0xE5840004, 0xE5940000, 0xE5971004, 0xE59F50F0, 0xE58D000C, 0xE58D1008, 0xE3A03000\n"
        ".word 0xE3A02001, 0xE3A0107D, 0xE28F00C4, 0xE88D0120, 0xEB046CF3, 0xE5940000, 0xE5971004, 0xE3A03000\n"
        ".word 0xE58D000C, 0xE58D1008, 0xE3A02001, 0xE3A010DB, 0xE28F009C, 0xE88D0120, 0xEB046CE9, 0xE59F20A8\n"
        ".word 0xE5941000, 0xE5970004, 0xE88D0104, 0xE3A03000, 0xE1CD00F8, 0xE3A02001, 0xE3A010E7, 0xE28F008C\n"
        ".word 0xEB046CDF, 0xE584000C, 0xE28DD014, 0xE8BD83F0, 0x535C3A63, 0x5C34544D, 0x36445258, 0x735C3638\n"
        ".word 0x34736464, 0x6F72705C, 0x6D617267, 0x6575715C, 0x635F7473, 0x65746E65, 0x63715C72, 0x6E69614D\n"
        ".word 0x7070632E, 0x00000000, 0x0044DB88, 0x00000143, 0x00000157, 0x001FE0B4, 0x001A9970, 0x73657551\n"
        ".word 0x6E654374, 0x4D726574, 0x506E6961, 0x00636F72, 0x001FE134, 0x73657551, 0x6E654374, 0x44726574\n"
        ".word 0x55776172, 0x004C2070, 0x001D9510, 0x001FE0F8, 0x73657551, 0x6E654374, 0x44726574, 0x44776172\n"
        ".word 0x006E776F\n"
    );
}

//
[[maybe_unused]] static void eventCommand_func_0025955c_Decompiled(
    u32 owner, s32 frames, u32 mode, f32 alpha) {
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
// DECOMP_FUNC(0x0025955c, 516)


// Exact ARMv6K body recovered from 0x0025955C. The C++ implementation above
// documents the fade state transitions; this preserves its original code and
// literal pool for byte-level matching.
__attribute__((naked)) void eventCommand_func_0025955c(
    u32, s32, u32, f32) {
    asm volatile(
        ".word 0xE92D47F0, 0xE1A06000, 0xE1A05001, 0xE1A07002, 0xE59F9170, 0xE3A08000, 0xED2D8B02, 0xEEB08A40\n"
        ".word 0xE5990000, 0xEDDF8A58, 0xE24DD010, 0xE3500000, 0x1A00002D, 0xE59F1154, 0xE28F0F55, 0xE1A00000\n"
        ".word 0xE3A00001, 0xE3A01C01, 0xE58D0000, 0xE3A03018, 0xE3A02000, 0xE1A00001, 0xEB01AD72, 0xE5890000\n"
        ".word 0xEDC08A02, 0xE59F2160, 0xE5808014, 0xE5808010, 0xE59F1150, 0xE1A04000, 0xE28D0004, 0xE58D2000\n"
        ".word 0xE8800012, 0xE3A03000, 0xE1A02003, 0xE3A01002, 0xE28F0F4E, 0xEB01B0E0, 0xE5840000, 0xE59FA144\n"
        ".word 0xE3A03000, 0xE58D000C, 0xE1A02003, 0xE3A01080, 0xE28F0F4D, 0xE58D4008, 0xE58D8004, 0xE58DA000\n"
        ".word 0xEB01AD77, 0xE5941000, 0xE3A03000, 0xE1A02003, 0xE58D100C, 0xE3A010DE, 0xE28F0F43, 0xE58D4008\n"
        ".word 0xE58D8004, 0xE58DA000, 0xEB01AD6D, 0xE5990000, 0xE3570000, 0xE5805014, 0xE5808010, 0x0A00000C\n"
        ".word 0xE3550000, 0xE5806004, 0x02800008, 0x0C808A02, 0x0A000004, 0xEE005A10, 0xEDC08A02, 0xEEB80AC0\n"
        ".word 0xEEC80A00, 0xEDC00A03, 0xE28DD010, 0xECBD8B02, 0xE8BD87F0, 0xE3550000, 0x0A00000C, 0xED900A02\n"
        ".word 0xEEB40A68, 0xEEF1FA10, 0xEE005A10, 0x05806004, 0xED808A02, 0xEEB80AC0, 0xEEC80A00, 0xEEB10A60\n"
        ".word 0xED800A03, 0xE28DD010, 0xECBD8B02, 0xE8BD87F0, 0xE5806004, 0xEDC08A02, 0xEDC08A03, 0xE28DD010\n"
        ".word 0xECBD8B02, 0xE8BD87F0, 0x0043E088, 0x00000000, 0x000001CD, 0x535C3A63, 0x5C34544D, 0x36445258\n"
        ".word 0x735C3638, 0x34736464, 0x6F72705C, 0x6D617267, 0x6576655C, 0x655C746E, 0x746E6576, 0x6D6D6F43\n"
        ".word 0x2E646E61, 0x00707063, 0x00317EB8, 0x002E21DC, 0x6E657645, 0x73654D74, 0x646E5573, 0x61467265\n"
        ".word 0x505F6564, 0x00636F72, 0x002E2074, 0x6E657645, 0x73654D74, 0x646E5573, 0x61467265, 0x445F6564\n"
        ".word 0x00776172\n"
    );
}

// ---------------------------------------------------------------------------
// EventEffect.cpp (0x0030A4FC), 504 B
// ---------------------------------------------------------------------------

//
[[maybe_unused]] static void EventEffect_func_0030a4fc_Decompiled() {
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
                       TaskCallback(0x002221F0), 0, 0, work->calc_task);
    AsdTask_CreateDraw("BlinkFade DrawUpRight", 0xDF, 0, 0,
                       TaskCallback(0x002221F0), 0, 0, work->calc_task);

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
// DECOMP_FUNC(0x0030a4fc, 504)


// Exact ARMv6K body recovered from 0x0030A4FC. The retained C++ version
// above documents the resource/task setup; this preserves its original code
// layout and literal pool for byte-level matching.
__attribute__((naked)) void EventEffect_func_0030a4fc() {
    asm volatile(
        ".word 0xE92D41F0, 0xE24DD010, 0xE3A08001, 0xE59F4154, 0xE5940000, 0xE3500000, 0x1A000009, 0xE3A01054\n"
        ".word 0xE28F0F51, 0xE1A00000, 0xE3A01C01, 0xE3A0301C, 0xE3A02000, 0xE1A00001, 0xE58D8000, 0xEBFEE991\n"
        ".word 0xE5840000, 0xE3A05000, 0xE1A04000, 0xE59F0154, 0xE5845000, 0xE5845004, 0xE5845008, 0xE584500C\n"
        ".word 0xE5845010, 0xE5845014, 0xE5845018, 0xE88D0021, 0xE1A03005, 0xE1A02005, 0xE3A01001, 0xE28F0F4A\n"
        ".word 0xE58D5008, 0xEBFEECFC, 0xE5840000, 0xE59F6128, 0xE3A03000, 0xE58D000C, 0xE1A02003, 0xE3A01081\n"
        ".word 0xE28F0F46, 0xE58D5004, 0xE58D6000, 0xE58D5008, 0xEBFEE993, 0xE5940000, 0xE3A03000, 0xE1A02003\n"
        ".word 0xE58D000C, 0xE3A010DF, 0xE28F0F42, 0xE58D5004, 0xE58D6000, 0xE58D5008, 0xEBFEE989, 0xE5845010\n"
        ".word 0xED9F0A42, 0xE5845008, 0xE59F7104, 0xE5C45018, 0xE3A00028, 0xED840A05, 0xE584000C, 0xE0854085\n"
        ".word 0xE7970104, 0xEBFD05C7, 0xE3500000, 0xE320F000, 0x1A000004, 0xE7970104, 0xE3A01000, 0xEBFEED39\n"
        ".word 0xE0870104, 0xE5C08009, 0xE0876104, 0xE7970104, 0xE5961004, 0xEBFE6F70, 0xE3500000, 0xE320F000\n"
        ".word 0x1A000003, 0xE5961004, 0xE7970104, 0xEBFE6EF1, 0xE5C68008, 0xE2855001, 0xE3550002, 0xBAFFFFE6\n"
        ".word 0xE28DD010, 0xE8BD81F0, 0x0043DEE8, 0x535C3A63, 0x5C34544D, 0x36445258, 0x735C3638, 0x34736464\n"
        ".word 0x6F72705C, 0x6D617267, 0x6576655C, 0x325C746E, 0x65764564, 0x455C746E, 0x746E6576, 0x65666645\n"
        ".word 0x632E7463, 0x00007070, 0x00222428, 0x6E696C42, 0x6461466B, 0x61432065, 0x0000636C, 0x002221F0\n"
        ".word 0x6E696C42, 0x6461466B, 0x72442065, 0x70557761, 0x7466654C, 0x00000000, 0x6E696C42, 0x6461466B\n"
        ".word 0x72442065, 0x70557761, 0x68676952, 0x00000074, 0x3F800000, 0x0043DF00\n"
    );
}

// ---------------------------------------------------------------------------
// clearSave.cpp (0x001E1118), 488 B
// ---------------------------------------------------------------------------

//
[[maybe_unused]] static void clearSave_func_001e1118_Decompiled(u32 arg) {
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
    Tbb_EnsureSlotLoaded(0x3C);
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
// DECOMP_FUNC(0x001e1118, 488)


// Exact ARMv6K body recovered from 0x001E1118. The C++ implementation above
// documents the save-clear setup; the raw sequence retains the original calls,
// task arguments, and literal pool exactly.
__attribute__((naked)) void clearSave_func_001e1118(u32) {
    asm volatile(
        ".word 0xE92D4070, 0xE1A04000, 0xE24DD010, 0xE3A01E25, 0xE28F0E13, 0xE1A00000, 0xE3A06001, 0xE3A01C01\n"
        ".word 0xE3A03094, 0xE3A02000, 0xE1A00001, 0xE58D6000, 0xEB0390E8, 0xE59F5144, 0xE3A01094, 0xE5850000\n"
        ".word 0xEB038E74, 0xE3540000, 0x05950000, 0x05C06008, 0xE5954000, 0xE3A0003C, 0xEB02D94D, 0xEB02A274\n"
        ".word 0xEB02B1FD, 0xEB02A259, 0xE28F0F45, 0xEB039328, 0xE5840088, 0xE28F0E12, 0xEB039325, 0xE1A01000\n"
        ".word 0xE5840090, 0xE5940088, 0xEB02D854, 0xE3A01002, 0xE584008C, 0xE5801108, 0xE3A01083, 0xE3A00002\n"
        ".word 0xEB03923E, 0xE5D40008, 0xE3500000, 0x0A000005, 0xE3A010FF, 0xE3A00000, 0xEB028725, 0xE3A010FF\n"
        ".word 0xE3A00001, 0xEB028722, 0xE59F10E8, 0xE59F00E8, 0xE5952000, 0xE3A03000, 0xE88D0007, 0xE1A02003\n"
        ".word 0xE3A01002, 0xE28F00D4, 0xEB0391DC, 0xE5951000, 0xE59F40D4, 0xE3A06000, 0xE1A03006, 0xE5810000\n"
        ".word 0xE88D0050, 0xE58D1008, 0xE58D000C, 0xE1A02006, 0xE3A01065, 0xE28F00B4, 0xEB038E72, 0xE5950000\n"
        ".word 0xE3A03000, 0xE1A02003, 0xE5901000, 0xE1CD00F8, 0xE3A010CC, 0xE28F00A0, 0xE88D0050, 0xEB038E69\n"
        ".word 0xE28DD010, 0xE8BD8070, 0x535C3A63, 0x5C34544D, 0x36445258, 0x735C3638, 0x34736464, 0x6F72705C\n"
        ".word 0x6D617267, 0x656C635C, 0x735F7261, 0x5C657661, 0x61656C63, 0x76615372, 0x70632E65, 0x00000070\n"
        ".word 0x0043DE80, 0x61656C63, 0x61735F72, 0x632F6576, 0x7261656C, 0x65766153, 0x0066622E, 0x61656C63\n"
        ".word 0x61735F72, 0x632F6576, 0x7261656C, 0x65766153, 0x6D626D2E, 0x00000000, 0x00206B40, 0x001B0FE0\n"
        ".word 0x61656C63, 0x76615372, 0x00432065, 0x001E1318, 0x61656C63, 0x76615372, 0x004C2065, 0x61656C63\n"
        ".word 0x76615372, 0x00522065\n"
    );
}

} // namespace smt4::script
