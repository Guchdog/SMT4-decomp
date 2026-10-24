#include "camp/unite_extras.h"
#include "engine/asd_symbols.h"
#include "ui/tbb_table.h"

#include <cstdint>

namespace smt4::camp {

// ---------------------------------------------------------------------------
// Globals (addresses are the storage locations used by the listing)
// ---------------------------------------------------------------------------

BibleDevilManager g_BibleDevilManager = {nullptr, 0};                  // 0x0043D9C8 (.data, zero)
BibleLegionDrawManager g_BibleLegionDrawManager = {0, 0, {0, 0}, nullptr}; // 0x0043D9E0 (.data, zero)
BibleLegionSkillManager g_BibleLegionSkillManager = {nullptr};         // 0x0043D9F8 (.data, zero)

namespace {

inline u8* At(void* base, u32 offset) {
    return static_cast<u8*>(base) + offset;
}

inline void (*TaskCallback(u32 address))(void*) {
    return reinterpret_cast<void (*)(void*)>(
        static_cast<std::uintptr_t>(address));
}

template <typename T>
inline u32 AddressOf(T pointer) {
    return static_cast<u32>(reinterpret_cast<std::uintptr_t>(pointer));
}

} // namespace

// ---------------------------------------------------------------------------
// Observed call targets (addresses are the branch targets in code.bin)
// ---------------------------------------------------------------------------

extern "C" {
    // AsdMemory (c:\SMT4\XRD686\AsdSDK\Source\Sys\Mem\AsdMemory.cpp)
    void* AsdMem_Alloc(u32 a0, u32 a1, u32 a2, u32 size, u32 flag);        // 0x002C4B84
    void  AsdMem_Zero(void* ptr, u32 size);                                // 0x002C4B30

    // 0x002B9364 is declared canonically as Battle_GetTalkEntry in
    // engine/asd_symbols.h.

    // 0x0029ED08 (60 B): compendium-owned predicate for a demon id.
    u32   camp_func_0029ed08(u32 demon_id);

    // 0x0022E310 (384 B): fill the 0x20-byte result entry from the row and
    // (mode != 0) the 0x604-byte gamedata record.
    void  camp_func_0022e310(UnitePickEntry* out, u32 id, u32 mode);

    // 0x0029D100 (1984 B): build one text/status row; fifth argument is the
    // stack word at [sp] (always 0 at both call sites).
    u32   camp_func_0029d100(u32 id, u32 mode, u32 a2, u32 a3, u32 a4);

    // 0x0022E2EC (36 B): list->entries[list->count] = *entry; ++list->count.
    void  unite_func_0022e2ec(UnitePickList* list, const UnitePickEntry* entry);

    // 0x0022E490 (88 B): reset the list header / 0x500 slots / capacity.
    void  unite_func_0022e490(UnitePickList* list);

    // 0x0022E244 (76 B): (count * 100) / capacity clamped to [1, 100].
    u8    unite_func_0022e244(UnitePickList* list);

    // 0x0022E290 (92 B): cache mode at +0xA004 and qsort the slots.
    void  unite_func_0022e290(UnitePickList* list, s8 mode);

    // 0x002A0FAC (24 B): global configuration byte block; the listing loads
    // the pre-indexed `ldrb r1,[r0,#0xf]!` sort selector at +0xF.
    u8*   camp_func_002a0fac();

    // 0x002A8A08 (20 B): gamedata base (`*(0x0043E2A8+4) + 0x8C`).
    u8*   camp_func_002a8a08();

    // 0x002CD2CC (716 B): gamedata record predicate; non-zero = skip.
    u32   camp_func_002cd2cc(const UniteGamedataRecord* record);

    // 0x003AD8C0 (12 B): available * 100 / total, 0 when total <= 0.
    s32   unite_func_003ad8c0(s32 available, s32 total);

    // 0x002339E8 / 0x002339AC (60 B each): clear a UI list's s16 count at
    // +0x5A / +0x30 (calling 0x002B9008 once per entry) and zero it.
    void  shop_func_002339e8(UniteUiList* list);
    void  shop_func_002339ac(UniteResultRows* rows);

    // 0x002338C4 (216 B): reset the result panel at work+0x20; the 6th/7th
    // arguments are the two stack words (both 1 at 0x0022D728).
    void  unite_func_002338c4(void* panel, u32 a1, s32 a2, u32 a3, u32 a4, u32 a5);

    // 0x00233804 (168 B): fill a UniteResultRows block (0x1D / 0x40E / count).
    void  unite_func_00233804(UniteResultRows* rows, u32 a1, u32 a2, s32 count);

    // 0x002338AC (24 B): min(panel+4, panel+8), i.e. min(0xA, list count).
    s32   unite_func_002338ac(const void* panel);

    // 0x0022DF7C (140 B): mark a demon id in the 16-slot selection arrays.
    void  unite_func_0022df7c(u16* ids, u16 demon_id);

    // 0x003AAD60 (56 B): fill 16 ids with -1 and the 16 flags at +0x20 with 0.
    void  unite_func_003aad60(u16* ids);

    // 0x00233600 (396 B): build the 0x480-byte sprite group at work+0xDC.
    void  unite_func_00233600(void* sprite_group);

    // 0x002333D4 (168 B): per-slot sprite highlight switch.
    void  shop_func_002333d4(void* sprite_group, u32 index);

    // 0x00232800 (44 B): initialise a UI rect (x=0x140, y=0, w=0, h=0, id=0x1D).
    void  unite_func_00232800(void* panel, s32 x, s32 y, u32 id);

    // 0x002333BC (24 B): base constructor (vtable 0x004221E4, u16 +4 = 0).
    void  unite_func_002333bc(void* object);

    // 0x002C3344 / 0x002C32F8 are declared canonically as UiSpriteGroup_Init
    // and UiSpriteGroup_BindTable in engine/asd_symbols.h.

    // 0x002BDB2C (152 B): reset + initialise one 0x8C-byte sprite node.
    void  camp_func_002bdb2c(void* sprite, u32 a1, u32 a2, void* a3, f32 scale,
                             u32 a5);

    // 0x002AF854 (64 B): attach a table row to a sprite node.
    void  battle_func_002af854(void* sprite, u32 a1, u32 a2);

    // 0x002C0BCC is declared canonically as Random_Range in
    // engine/asd_symbols.h.

    // 0x002C615C (556 B): unsigned division (r0 / r1); second argument is the
    // divisor loaded from the list capacity at 0x0022E250.
    u32   ui_func_002c615c(u32 numerator, u32 denominator);

    // 0x0029E01C (100 B): set the status mode / refresh affinity table.
    void  camp_func_0029e01c(u32 mode);

    // 0x0029F10C (316 B): reset the ButtonHelp workspace and store the colour.
    void  camp_func_0029f10c(u32 mode, u32 color);

    // 0x002E32C8 (60 B): release the global +0x941CC object.
    void  unite_func_002e32c8();

    // 0x0022D33C (652 B): refresh the result row text; tail-called at the end
    // of bibleDevil_func_003a7ad8 (`b #0x22d33c`, 0x003A7CE4).
    void  camp_func_0022d33c(UniteExtrasWork* work);

    // 0x003ACD48 (80 B): bring up TMT texture slot 0x22 once and bump the
    // LegionDraw manager's +1 ref count.
    void  engine_func_003acd48();

    // 0x003AAF30 (40 B): calc-task teardown; frees the 0x0043D9C8 handle.
    void  engine_func_003aaf30(void* handle);

    // 0x003AD05C (40 B): calc-task teardown; frees the 0x0043D9F8 handle.
    void  engine_func_003ad05c(void* handle);

    // 0x003AB0D0 (424 B): fill the result list from table ids 0x79F..0x802.
    void  unite_func_003ab0d0(UniteExtrasWork* work);

    // 0x002B7F0A (152 B): qsort(base, count, size, compar).
    void  qsort_arm(void* base, s32 nmemb, u32 size,
                    s32 (*compar)(const void*, const void*));

    // 0x00219600: ascending by {value at +2, id at +0}.
    s32   func_00219600(const void* a, const void* b);
}

// ===========================================================================
// Unite result list builder (Unite.cpp)
// ===========================================================================

//
[[maybe_unused]] static void unite_func_0022d5c8_Decompiled(
    UniteExtrasWork* work) {
    UniteUiList* ui = work->ui_list;                                      // +0x590 (fp)
    shop_func_002339e8(ui);                                               // 0x0022D5DC
    UniteResultRows* rows = &work->result_rows;                           // work+0x55C
    shop_func_002339ac(rows);                                             // 0x0022D5EC
    UnitePickList* list = &work->list;                                    // work+0x5A8

    if (work->list_mode == 1) {                                           // 0x0022D5FC/0x0022D60C
        // Legion roster path: walk the 27 gamedata slots at base+0x90F0.
        unite_func_0022e490(list);                                        // 0x0022D7C4
        const u8* base = camp_func_002a8a08();                            // 0x0022D7D0
        u32 roster_count = base[0x910B];                                  // 0x0022D7DC
        for (u32 i = 0; i < roster_count; ++i) {                          // 0x0022D7E4 bhi
            s8 slot = static_cast<s8>(base[0x90F0 + i]);                  // 0x0022D7F4 ldrsb
            if (slot < 0) {
                continue;                                                 // 0x0022D7FC
            }
            const UniteGamedataRecord* record =
                reinterpret_cast<const UniteGamedataRecord*>(
                    base + 0x90 + static_cast<u32>(slot) * 0x604);        // 0x0022D800..0x0022D810
            if (camp_func_002cd2cc(record) != 0) {
                continue;                                                 // 0x0022D820
            }
            const UniteBibleRow* row =
                static_cast<const UniteBibleRow*>(
                    Battle_GetTalkEntry(record->demon_id));              // 0x0022D828
            UnitePickEntry entry{};                                       // sp+0x10
            camp_func_0022e310(&entry, row->id, 1);                       // 0x0022D83C
            entry.field_08 = camp_func_0029d100(
                row->id, work->sort_mode, 0,
                work->completion >= 0x64 ? 1u : 0u, 0);                   // 0x0022D864..0x0022D868
            unite_func_0022e2ec(list, &entry);                            // 0x0022D874
        }

        list->capacity = 0x18;                                            // 0x0022D890
        unite_func_002338c4(At(work, 0x20), 0xA,
                            static_cast<s16>(list->count), 0, 1, 1);      // 0x0022D8B0
        work->result_field_02d = 1;                                       // 0x0022D8C8
        s32 available = 0;                                                // r7
        s32 total = 0;                                                    // r6
        for (u32 i = 0; i < 0x4FF; ++i) {                                 // 0x0022D8D4 blt
            const UniteBibleRow* row = static_cast<const UniteBibleRow*>(
                Battle_GetTalkEntry(static_cast<u16>(i + 1)));        // 0x0022D8DC
            if (row == nullptr) {
                continue;                                                 // 0x0022D8E8
            }
            if ((row->flags & 1) == 0) {
                continue;                                                 // 0x0022D8F4
            }
            ++total;                                                      // 0x0022D8FC
            if (camp_func_0029ed08(row->id) != 0) {
                ++available;                                              // 0x0022D908
            }
        }
        work->completion = static_cast<s8>(
            unite_func_003ad8c0(available, total));                       // 0x0022D920
        AsdSound_GetTableEntry(0);                                        // 0x0022D92C
    } else {
        unite_func_0022e490(list);                                        // 0x0022D610
        u32 available = 0;                                                // r7
        for (u32 i = 0; i < 0x4FF; ++i) {                                 // r8 = 0x4FF, bgt
            const UniteBibleRow* row = static_cast<const UniteBibleRow*>(
                Battle_GetTalkEntry(static_cast<u16>(i + 1)));        // 0x0022D628
            if (row == nullptr) {
                continue;                                                 // 0x0022D634
            }
            if ((row->flags & 1) == 0) {
                continue;                                                 // 0x0022D640
            }
            ++available;                                                  // 0x0022D648
            if (camp_func_0029ed08(row->id) == 0) {
                continue;                                                 // 0x0022D658
            }
            UnitePickEntry entry{};                                       // sp+0x10
            camp_func_0022e310(&entry, row->id, 0);                       // 0x0022D668
            entry.field_08 = camp_func_0029d100(
                row->id, work->sort_mode, 0,
                work->completion >= 0x64 ? 1u : 0u, 0);                   // 0x0022D690..0x0022D694
            unite_func_0022e2ec(list, &entry);                            // 0x0022D6A0
        }

        list->capacity = static_cast<s16>(available);                     // 0x0022D6B0
        if (list->count != 0) {                                           // 0x0022D6B4
            // `ldrb r1,[r0,#0xf]!` (0x0022D6C4): the selector byte is both
            // the comparator index and, in the default arm, a mode value.
            u8* selector = camp_func_002a0fac() + 0xF;                    // 0x0022D6C0
            u8 raw = *selector;
            s8 sort_mode;
            switch (raw & 0x7F) {
                case 1:  sort_mode = 6;    break;                         // 0x0022D6D0
                case 2:  sort_mode = 4;    break;                         // 0x0022D6DC
                case 3:  sort_mode = 0x16; break;                         // 0x0022D6E8
                case 7:  sort_mode = 0x18; break;                         // 0x0022D6F4
                default:
                    *selector = static_cast<u8>((raw & 0x80) | 1);        // 0x0022D6FC..0x0022D708
                    sort_mode = 6;
                    break;
            }
            raw = *selector;                                              // 0x0022D70C
            if ((raw & 0x80) != 0) {
                sort_mode = static_cast<s8>(sort_mode + 1);               // 0x0022D714/0x0022D718
            }
            unite_func_0022e290(list, sort_mode);                         // 0x0022D720
        }
        unite_func_002338c4(At(work, 0x20), 0xA,
                            static_cast<s16>(list->count), 0, 1, 1);      // 0x0022D740
        work->result_field_02d = 1;                                       // 0x0022D750
        work->completion = static_cast<s8>(unite_func_0022e244(list));    // 0x0022D75C
        AsdSound_GetTableEntry(0);                                        // 0x0022D764
    }

    // Common tail (0x0022D768..0x0022D7BC), entered from both paths.
    void** vtable = ui->vtable;                                           // 0x0022D76C
    reinterpret_cast<void (*)(void*)>(
        reinterpret_cast<std::uintptr_t>(vtable[2]))(At(work, 0x20));      // 0x0022D778
    u16* flags = reinterpret_cast<u16*>(At(ui, 4));                       // 0x0022D784
    *flags = static_cast<u16>(*flags | 0x1000);                           // 0x0022D78C
    s32 rows_count = work->result_count;                                  // 0x0022D790
    if (rows_count >= 0xA) {
        rows_count = 0xA;                                                 // 0x0022D7A0
    }
    unite_func_00233804(rows, 0x1D, 0x40E, rows_count);                   // 0x0022D7A4
    rows->enabled = 1;                                                    // 0x0022D7AC (work+0x56C)
    AsdSound_GetTableEntry(0);                                            // tail b 0x002C583C
}

// ===========================================================================
// Bible Devil setup (bibleDevil.cpp)
// ===========================================================================

//
[[maybe_unused]] static void bibleDevil_func_003a7ad8_Decompiled(
    UniteExtrasWork* work) {
    work->sort_mode = 1;                                                  // 0x003A7AF4 (work+0x5A5)
    work->completion = 0;                                                 // 0x003A7B00
    work->field_a5b2 = -1;                                                // 0x003A7B04
    work->field_a5b0 = 0;                                                 // 0x003A7B08

    unite_func_0022e490(&work->list);                                     // 0x003A7B18

    void** vtable = work->vtable;                                         // 0x003A7B1C
    reinterpret_cast<void (*)(void*)>(
        reinterpret_cast<std::uintptr_t>(vtable[8]))(work);               // 0x003A7B28 ([vtable+0x20])

    camp_func_0029e01c(2);                                                // 0x003A7B30

    // 4-byte task user handle at 0x0043D9C8; [0] receives the work pointer.
    void** handle = static_cast<void**>(AsdMem_Alloc(0x100, 0x100, 0, 4, 1)); // 0x003A7B54
    g_BibleDevilManager.work_handle = handle;                             // 0x003A7B68
    handle[0] = work;                                                     // 0x003A7B6C

    work->calc_task = AsdTask_CreateCalc(
        "BIBLE DEVIL CALC", 2, 0, 0,
        TaskCallback(0x003aaf08),
        AddressOf(engine_func_003aaf30),
        AddressOf(handle));                                               // 0x003A7B88
    work->draw_up_task = AsdTask_CreateDraw(
        "BIBLE DEVIL UP", 0x6F, 1, 0,
        TaskCallback(0x003ac958), 0, AddressOf(handle), work->calc_task);            // 0x003A7BB4
    work->draw_down_task = AsdTask_CreateDraw(
        "BIBLE DEVIL DOWN", 0xE6, 1, 0,
        TaskCallback(0x003acc74), 0, AddressOf(handle), work->calc_task);            // 0x003A7BE4

    unite_func_00232800(At(work, 0xC8), 0x140, 0, 0x1D);                  // 0x003A7BFC

    void* ui = engine::AsdMemory_func_002c23f8(0x68);                     // 0x003A7C08
    if (ui != nullptr) {                                                  // 0x003A7C10
        unite_func_002333bc(ui);                                          // 0x003A7C14
        *static_cast<void**>(ui) = reinterpret_cast<void*>(
            static_cast<std::uintptr_t>(0x0042207Cu));                    // 0x003A7C1C
    }
    work->ui_list = static_cast<UniteUiList*>(ui);                        // 0x003A7C24
    *reinterpret_cast<void**>(At(ui, 0x64)) = At(work, 0xC8);             // 0x003A7C28

    unite_func_0022d5c8(work);                                            // 0x003A7C30

    unite_func_003aad60(work->selected_ids);                              // 0x003A7C3C
    unite_func_0022df7c(work->selected_ids, 0);                           // 0x003A7C48

    s32 visible = unite_func_002338ac(At(work, 0x20));                    // 0x003A7C54
    for (s32 i = 0; i < visible; ++i) {                                   // 0x003A7C60
        // `ldrsh r0,[r7,r4,lsl #5]` with r7 = work+0x5A8, i.e. entry id at
        // list+0x04+i*0x20 (the list's first entry).
        s16 demon_id = static_cast<s16>(work->list.entries[i].demon_id);
        if (demon_id != 0) {                                              // 0x003A7C70
            unite_func_0022df7c(work->selected_ids,
                                static_cast<u16>(demon_id));              // 0x003A7C7C
        }
    }

    unite_func_00233600(At(work, 0xDC));                                  // 0x003A7C90

    s32 rows_count = work->result_count;                                  // 0x003A7C94
    if (rows_count >= 0xA) {
        rows_count = 0xA;                                                 // 0x003A7CA4
    }
    unite_func_00233804(&work->result_rows, 0x1D, 0x40E, rows_count);     // 0x003A7CB0

    work->result_rows.enabled = 1;                                        // 0x003A7CBC (work+0x56C)
    camp_func_0029f10c(0, 0x323232FF);                                    // 0x003A7CC0
    work->field_014 = 0;                                                  // 0x003A7CC4
    work->field_018 = 0;                                                  // 0x003A7CC8
    unite_func_002e32c8();                                                // 0x003A7CCC
    g_BibleDevilManager.field_04 = -1;                                    // 0x003A7CD4

    camp_func_0022d33c(work);                                             // tail b 0x003A7CE4
}

// ===========================================================================
// Bible LegionSkill setup (bibleLegionSkill.cpp)
// ===========================================================================

//
[[maybe_unused]] static void bibleLegionSkill_func_003ab770_Decompiled(
    UniteExtrasWork* work) {
    work->field_014 = 0;                                                  // 0x003AB784
    work->field_018 = 0;                                                  // 0x003AB78C
    work->completion = 0;                                                 // 0x003AB790
    work->field_a5b0 = 0;                                                 // 0x003AB794

    unite_func_0022e490(&work->list);                                     // 0x003AB7A0

    void** vtable = work->vtable;                                         // 0x003AB7A4
    reinterpret_cast<void (*)(void*)>(
        reinterpret_cast<std::uintptr_t>(vtable[8]))(work);               // 0x003AB7B0 ([vtable+0x20])

    engine_func_003acd48();                                               // 0x003AB7B4

    // 4-byte task user handle at 0x0043D9F8; [0] receives the work pointer.
    void** handle = static_cast<void**>(AsdMem_Alloc(0x100, 0x100, 0, 4, 1)); // 0x003AB7DC
    g_BibleLegionSkillManager.work_handle = handle;                       // 0x003AB7F0
    handle[0] = work;                                                     // 0x003AB7F4

    work->calc_task = AsdTask_CreateCalc(
        "BIBLE LEGIONSKILL CALC", 2, 0, 0,
        TaskCallback(0x003ad034),
        AddressOf(engine_func_003ad05c),
        AddressOf(handle));                                               // 0x003AB810
    work->draw_up_task = AsdTask_CreateDraw(
        "BIBLE LEGIONSKILL UP", 0x6F, 1, 0,
        TaskCallback(0x003ad288), 0, AddressOf(handle), work->calc_task);            // 0x003AB83C
    work->draw_down_task = AsdTask_CreateDraw(
        "BIBLE LEGIONSKILL DOWN", 0xE6, 1, 0,
        TaskCallback(0x003ad588), 0, AddressOf(handle), work->calc_task);            // 0x003AB86C

    unite_func_00232800(At(work, 0xC8), 0x140, 0, 0x1D);                  // 0x003AB884
    unite_func_00233600(At(work, 0xDC));                                  // 0x003AB88C
    shop_func_002333d4(At(work, 0xDC), 0);                                // 0x003AB898
    shop_func_002333d4(At(work, 0xDC), 1);                                // 0x003AB8A4

    void* ui = engine::AsdMemory_func_002c23f8(0x68);                     // 0x003AB8B0
    if (ui != nullptr) {                                                  // 0x003AB8B8
        unite_func_002333bc(ui);                                          // 0x003AB8BC
        *static_cast<void**>(ui) = reinterpret_cast<void*>(
            static_cast<std::uintptr_t>(0x0042207Cu));                    // 0x003AB8C4
    }
    work->ui_list = static_cast<UniteUiList*>(ui);                        // 0x003AB8CC
    *reinterpret_cast<void**>(At(ui, 0x64)) = At(work, 0xC8);             // 0x003AB8D0

    unite_func_003ab0d0(work);                                            // 0x003AB8D8

    unite_func_00233804(&work->result_rows, 0x1D, 0x40E, 0xA);            // 0x003AB8F0
    work->result_rows.enabled = 1;                                        // 0x003AB8FC (work+0x56C)
    camp_func_0029f10c(0, 0x323232FF);                                    // 0x003AB900
    bibleLegionDraw_func_003ad300();                                      // 0x003AB90C (r0 dead)
    work->field_014 = 1;                                                  // 0x003AB910 `str r7,[r4,#0x14]!`
    work->field_018 = 0;                                                  // 0x003AB914 `str r6,[r4,#4]`
}

// ===========================================================================
// Bible LegionDraw manager (bibleLegionDraw.cpp)
// ===========================================================================

//
[[maybe_unused]] static void bibleLegionDraw_func_003ad300_Decompiled() {
    BibleLegionDrawManager* mgr = &g_BibleLegionDrawManager;              // 0x0043D9E0
    if (mgr->draw_ref_count > 0) {                                        // 0x003AD310/0x003AD318
        mgr->draw_ref_count = static_cast<s8>(
            static_cast<u8>(mgr->draw_ref_count) + 1);                   // 0x003AD4D4/0x003AD4D8
        return;
    }

    BibleLegionDrawWork* work = mgr->work;                                // 0x003AD31C
    if (work == nullptr) {                                                // 0x003AD328
        work = static_cast<BibleLegionDrawWork*>(
            AsdMem_Alloc(0x100, 0x100, 0, 0x474, 1));                     // 0x003AD354
        mgr->work = work;                                                 // 0x003AD358

        work->field_004 = 0;                                              // 0x003AD360
        work->field_008 = static_cast<s16>(-1);                           // 0x003AD364
        work->field_00c = 0;                                              // 0x003AD368
        work->field_010 = static_cast<s16>(-1);                           // 0x003AD36C
        work->field_014 = 0;                                              // 0x003AD370
        work->field_018 = static_cast<s16>(-1);                           // 0x003AD374
        work->field_01c = 0;                                              // 0x003AD37C
        work->field_01d = 0;                                              // 0x003AD380
        work->field_01f = 0;                                              // 0x003AD384
        work->field_01e = 0;                                              // 0x003AD38C
        work->field_270 = 0;                                              // 0x003AD398
        work->field_272 = 0;                                              // 0x003AD39C
        work->field_274 = 0.0f;                                           // 0x003AD3A0 (s17)
        work->field_27c = 1.0f;                                           // 0x003AD3A4 (s16)
        work->field_284 = 0;                                              // 0x003AD3AC
        work->field_288 = static_cast<u16>(Random_Range(0xC8) + 0x64);    // 0x003AD3B8
        work->field_278 = 0.0f;                                           // 0x003AD3C4 (s17)
        work->field_280 = -3.0f;                                          // 0x003AD3C8 (0xC0400000)
        work->field_286 = 0;                                              // 0x003AD3D0
        work->field_28a = static_cast<u16>(Random_Range(0xC8) + 0x64);    // 0x003AD3DC
        work->field_28c = 0;                                              // 0x003AD3C0
        work->field_28d = 0;                                              // 0x003AD3E8
        AsdMem_Zero(work->block_290, 0x1E0);                              // 0x003AD3EC
        work->field_470 = 0;                                              // 0x003AD378
    }

    work->calc_task = AsdTask_CreateCalc(
        "LegionDrawUp CALC", 2, 0, 0,
        TaskCallback(0x003ac6a0), 0, 0);                                  // 0x003AD410
    UiSpriteGroup_Init(At(work, 0x20));                                   // 0x003AD41C
    UiSpriteGroup_BindTable(
        At(work, 0x20), 0x00402414u, 0x24, 0x00402438u, 0x18,
        0, 0, 0, 0, 0x00402450u, 0x70);                                   // 0x003AD454

    for (u32 i = 0; i < 2; ++i) {                                         // 0x003AD4C8
        u8* node = At(work, i * 0x8C);                                    // `add r5,r6,r0,lsl #2`
        camp_func_002bdb2c(node + 0x40, 0x23, 0, At(work, 0x20), 1.0f, 0x15); // 0x003AD484
        battle_func_002af854(node + 0x40, 0, 0);                          // 0x003AD494
        camp_func_002bdb2c(node + 0x158, 0x23, 0, At(work, 0x20), 1.0f, 0x15); // 0x003AD4B0
        battle_func_002af854(node + 0x158, 1, 0);                         // 0x003AD4C0
    }

    mgr->draw_ref_count = static_cast<s8>(
        static_cast<u8>(mgr->draw_ref_count) + 1);                       // 0x003AD4D4/0x003AD4D8
}

// ===========================================================================
// UniteCtrl race buckets (UniteCtrl.cpp)
// ===========================================================================

//
[[maybe_unused]] static void UniteCtrl_func_003c9ebc_Decompiled(
    UniteCtrlRoster* roster) {
    const ui::Tbl1Header* table = ui::Tbb_GetGlobalSubTable(0, 0);         // 0x003C9ED0
    const void* payload = ui::Tbb_GetPayloadData(table);                  // 0x003C9ED8 (result dead)
    (void)payload;
    u32 row_count = ui::Tbb_GetRowCount(table);                           // 0x003C9EE4

    u8 local_counts[0x38];                                                // sp+0x08
    for (u32 i = 0; i < 0x38; ++i) {
        local_counts[i] = 0;                                              // 0x003C9EE8..0x003C9F1C
        roster->counts[i] = 0;                                            // 0x003C9F20..0x003C9F60
    }

    // Count available rows per race byte (row+0x02, 0..0x37).
    for (u32 i = 0; i < row_count; ++i) {                                 // 0x003C9F58/0x003C9F9C
        const UniteBibleRow* row = static_cast<const UniteBibleRow*>(
            Battle_GetTalkEntry(static_cast<u16>(i)));
        u32 race = row->race;
        if (race >= 0x38) {
            continue;                                                     // 0x003C9F74
        }
        if ((row->flags & 1) == 0) {
            continue;                                                     // 0x003C9F84
        }
        ++roster->counts[race];                                           // 0x003C9F88/0x003C9F90
    }

    // One 4-byte-entry array per class; empty classes keep a null pointer.
    for (u32 i = 0; i < 0x38; ++i) {                                      // 0x003C9FA0..0x003C9FF0
        void** slot = reinterpret_cast<void**>(&roster->buckets[i]);
        *slot = nullptr;                                                  // 0x003C9FAC
        u8 count = roster->counts[i];
        if (count != 0) {                                                 // 0x003C9FB8
            *slot = AsdMem_Alloc(0x100, 0x100, 0,
                                 static_cast<u32>(count) << 2, 1);        // 0x003C9FE0
        }
    }

    // Fill {row id, row+0x03} in table order, per-class insertion index.
    if (row_count != 0) {                                                 // 0x003C9FF4
        u32 i = 0;
        do {
            const UniteBibleRow* row = static_cast<const UniteBibleRow*>(
                Battle_GetTalkEntry(static_cast<u16>(i)));
            u32 race = row->race;
            if (race < 0x38 && (row->flags & 1) != 0) {                   // 0x003C9F? (0x003CA014..0x3CA024)
                u8 index = local_counts[race];                            // 0x003CA02C
                UniteCtrlEntry* entries = roster->buckets[race];          // 0x003CA030
                entries[index].demon_id = row->id;                        // 0x003CA03C
                entries[index].field_02 = row->field_03;                  // 0x003CA058
                local_counts[race] = static_cast<u8>(index + 1);          // 0x003CA064/0x003CA068
            }
            ++i;
        } while (i < row_count);                                          // 0x003CA070
    }

    // Sort each non-empty bucket with the {+2, +0} ascending comparator.
    const u8* counts = roster->counts;                                    // r6 = roster
    for (u32 i = 0; i < 0x38; ++i) {                                      // r7 = 0x38 down
        UniteCtrlEntry* entries = roster->buckets[i];
        if (entries != nullptr) {                                         // 0x003CA090
            qsort_arm(entries, *counts, sizeof(UniteCtrlEntry),
                      func_00219600);                                     // 0x003CA0A0
        }
        ++counts;                                                         // 0x003CA0A8
    }

    // Tail state (0x003CA0B4..0x003CA110).
    roster->field_11c = 0;                                                // 0x003CA0B8
    roster->field_11e = 0;                                                // 0x003CA0BC
    roster->field_118 = 0;                                                // 0x003CA0C0
    roster->field_11a = 0;                                                // 0x003CA0C4
    roster->field_143 = 0;                                                // 0x003CA0C8
    roster->field_120 = 0;                                                // 0x003CA0CC
    roster->field_121 = 0;                                                // 0x003CA0D0
    for (u32 i = 0; i < 4; ++i) roster->field_122[i] = 0;                 // 0x003CA0D4
    for (u32 i = 0; i < 4; ++i) roster->field_126[i] = 0;                 // 0x003CA0D8
    for (u32 i = 0; i < 4; ++i) roster->field_12a[i] = 0;                 // 0x003CA0DC
    for (u32 i = 0; i < 4; ++i) roster->field_12e[i] = 0;                 // 0x003CA0E0
    roster->field_132 = 0;                                                // 0x003CA0E4
    roster->field_134 = static_cast<u16>(roster->field_134 & 0x03FF);     // 0x003CA0E8..0x003CA0F4 (bic #0xFC00)
    roster->field_136 = 0;                                                // 0x003CA0F8
    roster->field_138 = 0xFFFF;                                           // 0x003CA0FC
    roster->field_13a = 0xFFFF;                                           // 0x003CA100
    roster->field_17c = 0;                                                // 0x003CA104
}
// DECOMP_FUNC(0x003a7ad8, 668)


// Exact ARMv6K body recovered from 0x003A7AD8. The retained C++ body above
// documents the Bible Devil work setup; this preserves the original call and
// literal-pool layout for byte-level matching.
__attribute__((naked)) void bibleDevil_func_003a7ad8(UniteExtrasWork*) {
    asm volatile(
        ".word 0xE92D47F0, 0xE1A05000, 0xE24DD010, 0xE3A0A001, 0xE2802CA5, 0xE3A08000, 0xE2800A0A, 0xE5C5A5A5\n"
        ".word 0xE3E01000, 0xE2800E5B, 0xE5C58094, 0xE1C21BB2, 0xE5C08000, 0xE2850B01, 0xE2800F6A, 0xE1A07000\n"
        ".word 0xEBFA1A5C, 0xE5950000, 0xE5901020, 0xE1A00005, 0xE12FFF31, 0xE3A00002, 0xEBFBD939, 0xE3A010C8\n"
        ".word 0xE28F0F6A, 0xE1A00000, 0xE3A01C01, 0xE3A03004, 0xE3A02000, 0xE1A00001, 0xE58DA000, 0xEBFC740A\n"
        ".word 0xE59F91BC, 0xE59F11BC, 0xE59F21BC, 0xE3A03000, 0xE5890000, 0xE5805000, 0xE58D2000, 0xE58D1004\n"
        ".word 0xE58D0008, 0xE1A02003, 0xE3A01002, 0xE28F0F67, 0xEBFC777A, 0xE5850004, 0xE5992000, 0xE59F11A0\n"
        ".word 0xE58D000C, 0xE58D2008, 0xE88D0102, 0xE3A03000, 0xE3A02001, 0xE3A0106F, 0xE28F0F62, 0xEBFC7411\n"
        ".word 0xE5850008, 0xE5950004, 0xE5992000, 0xE59F1184, 0xE58D000C, 0xE58D2008, 0xE88D0102, 0xE3A03000\n"
        ".word 0xE3A02001, 0xE3A010E6, 0xE28F0F5B, 0xEBFC7405, 0xE585000C, 0xE3A0301D, 0xE3A02000, 0xE3A01D05\n"
        ".word 0xE28500C8, 0xEBFA2AFF, 0xE1A01004, 0xE3A00068, 0xEBFC69FA, 0xE3500000, 0x0A000002, 0xEBFA2DE8\n"
        ".word 0xE59F1148, 0xE5801000, 0xE28510C8, 0xE5850590, 0xE5801064, 0xE1A00005, 0xEBFA1664, 0xE2850096\n"
        ".word 0xE320F000, 0xEB000C47, 0xE3A01000, 0xE2850096, 0xEBFA18CB, 0xE2850020, 0xE320F000, 0xEBFA2F14\n"
        ".word 0xE2506000, 0xE3A04000, 0xDA000009, 0xE0870284, 0xE1D000F4, 0xE3500000, 0x0A000002, 0xE6FF1070\n"
        ".word 0xE2850096, 0xEBFA18BE, 0xE2844001, 0xE1540006, 0xBAFFFFF5, 0xE28500DC, 0xEBFA2E5A, 0xE5953028\n"
        ".word 0xE2850B01, 0xE59F20C8, 0xE353000A, 0xA3A0300A, 0xE3A0101D, 0xE2800F57, 0xEBFA2ED3, 0xE59F10B4\n"
        ".word 0xE3A00000, 0xE5C5A56C, 0xEBFBDD11, 0xE5858014, 0xE5858018, 0xEBFCED7D, 0xE3E00000, 0xE5890004\n"
        ".word 0xE28DD010, 0xE1A00005, 0xE8BD47F0, 0xEAFA1594, 0x535C3A63, 0x5C34544D, 0x36445258, 0x735C3638\n"
        ".word 0x34736464, 0x6F72705C, 0x6D617267, 0x6269625C, 0x625C656C, 0x656C6269, 0x69766544, 0x70632E6C\n"
        ".word 0x00000070, 0x0043D9C8, 0x003AAF30, 0x003AAF08, 0x4C424942, 0x45442045, 0x204C4956, 0x434C4143\n"
        ".word 0x00000000, 0x003AC958, 0x4C424942, 0x45442045, 0x204C4956, 0x00005055, 0x003ACC74, 0x4C424942\n"
        ".word 0x45442045, 0x204C4956, 0x4E574F44, 0x00000000, 0x0042207C, 0x0000040E, 0x323232FF\n"
    );
}
// DECOMP_FUNC(0x003ab770, 592)


// Exact ARMv6K body recovered from 0x003AB770. The retained C++ body above
// documents Legion Skill initialization and its UI/task registration.
__attribute__((naked)) void bibleLegionSkill_func_003ab770(UniteExtrasWork*) {
    asm volatile(
        ".word 0xE92D41D0, 0xE1A04000, 0xE24DD014, 0xE3A06000, 0xE2800A0A, 0xE5846014, 0xE2800E5B, 0xE5846018\n"
        ".word 0xE5C46094, 0xE5C06000, 0xE2840B01, 0xE2800F6A, 0xEBFA0B3A, 0xE5940000, 0xE5901020, 0xE1A00004\n"
        ".word 0xE12FFF31, 0xEB000563, 0xE3A010AD, 0xE28F0F57, 0xE1A00000, 0xE3A07001, 0xE3A01C01, 0xE3A03004\n"
        ".word 0xE3A02000, 0xE1A00001, 0xE58D7000, 0xEBFC64E8, 0xE59F8170, 0xE59F1170, 0xE59F2170, 0xE3A03000\n"
        ".word 0xE5880000, 0xE5804000, 0xE58D2000, 0xE58D1004, 0xE58D0008, 0xE1A02003, 0xE3A01002, 0xE28F0E15\n"
        ".word 0xEBFC6858, 0xE5840004, 0xE5982000, 0xE59F1158, 0xE58D000C, 0xE58D2008, 0xE88D0042, 0xE3A03000\n"
        ".word 0xE3A02001, 0xE3A0106F, 0xE28F0D05, 0xEBFC64EF, 0xE5840008, 0xE5940004, 0xE5982000, 0xE59F1144\n"
        ".word 0xE58D000C, 0xE58D2008, 0xE88D0042, 0xE3A03000, 0xE3A02001, 0xE3A010E6, 0xE28F0F4B, 0xEBFC64E3\n"
        ".word 0xE584000C, 0xE3A0301D, 0xE3A02000, 0xE3A01D05, 0xE28400C8, 0xEBFA1BDD, 0xE28400DC, 0xEBFA1F5B\n"
        ".word 0xE3A01000, 0xE28400DC, 0xEBFA1ECD, 0xE3A01001, 0xE28400DC, 0xEBFA1ECA, 0xE1A01005, 0xE3A00068\n"
        ".word 0xEBFC5AD0, 0xE3500000, 0x0A000002, 0xEBFA1EBE, 0xE59F10EC, 0xE5801000, 0xE28410C8, 0xE5840590\n"
        ".word 0xE5801064, 0xE1A00004, 0xEBFFFDFC, 0xE2840B01, 0xE59F20D0, 0xE3A0300A, 0xE3A0101D, 0xE2800F57\n"
        ".word 0xEBFA1FC3, 0xE59F10C0, 0xE3A00000, 0xE5C4756C, 0xEBFBCE01, 0xE320F000, 0xE320F000, 0xEB00067B\n"
        ".word 0xE5A47014, 0xE5846004, 0xE28DD014, 0xE8BD81D0, 0x535C3A63, 0x5C34544D, 0x36445258, 0x735C3638\n"
        ".word 0x34736464, 0x6F72705C, 0x6D617267, 0x6269625C, 0x625C656C, 0x656C6269, 0x6967654C, 0x6B536E6F\n"
        ".word 0x2E6C6C69, 0x00707063, 0x0043D9F8, 0x003AD05C, 0x003AD034, 0x4C424942, 0x454C2045, 0x4E4F4947\n"
        ".word 0x4C494B53, 0x4143204C, 0x0000434C, 0x003AD288, 0x4C424942, 0x454C2045, 0x4E4F4947, 0x4C494B53\n"
        ".word 0x5055204C, 0x00000000, 0x003AD588, 0x4C424942, 0x454C2045, 0x4E4F4947, 0x4C494B53, 0x4F44204C\n"
        ".word 0x00004E57, 0x0042207C, 0x0000040E, 0x323232FF\n"
    );
}
// DECOMP_FUNC(0x003ad300, 596)


// Exact ARMv6K body recovered from 0x003AD300. The C++ reference documents
// the Legion Draw manager's allocation, randomized fields, and sprite setup.
__attribute__((naked)) void bibleLegionDraw_func_003ad300() {
    asm volatile(
        ".word 0xE92D41F0, 0xE59F81DC, 0xED2D8B02, 0xE24DD020, 0xE1D800D0, 0xE3500000, 0xCA00006C, 0xE5980004\n"
        ".word 0xED9F8A71, 0xE3A07000, 0xE3500000, 0x1A00002F, 0xE59F11B8, 0xE28F0F6E, 0xE1A00000, 0xE3A00001\n"
        ".word 0xE3A01C01, 0xE58D0000, 0xE59F31DC, 0xE3A02000, 0xE1A00001, 0xEBFC5E0A, 0xE5880004, 0xE3E01000\n"
        ".word 0xE5807004, 0xE1C010B8, 0xE580700C, 0xE1C011B0, 0xE5807014, 0xE1C011B8, 0xE5C07470, 0xE5C0701C\n"
        ".word 0xE5C0701D, 0xE5C0701F, 0xE2805C02, 0xE5C0701E, 0xE1A04000, 0xEDDF8A65, 0xE1C577B0, 0xE1C577B2\n"
        ".word 0xEDC48A9D, 0xED848A9F, 0xE3A000C8, 0xE1C578B4, 0xEBFC4E05, 0xE2800064, 0xE1C508B8, 0xED9F0A5C\n"
        ".word 0xE5C4728C, 0xEDC48A9E, 0xED840AA0, 0xE3A000C8, 0xE1C578B6, 0xEBFC4DFC, 0xE2800064, 0xE1C508BA\n"
        ".word 0xE3A01E1E, 0xE2840E29, 0xE5C4728D, 0xEBFC5DCF, 0xE59F0140, 0xE5986004, 0xE3A03000, 0xE88D0081\n"
        ".word 0xE1A02003, 0xE3A01002, 0xE28F0F4B, 0xE58D7008, 0xEBFC6158, 0xE5860000, 0xE2860020, 0xEBFC57C8\n"
        ".word 0xE59F1128, 0xE3A00070, 0xE58D0018, 0xE58D1014, 0xE3A02018, 0xE58D700C, 0xE58D7010, 0xE88D0084\n"
        ".word 0xE2413018, 0xE3A02024, 0xE2431024, 0xE2860020, 0xE58D7008, 0xEBFC57A7, 0xE3A04000, 0xE3A07015\n"
        ".word 0xE0640184, 0xEEB00A48, 0xE0800100, 0xE2863020, 0xE0865100, 0xE2850040, 0xE3A02000, 0xE3A01023\n"
        ".word 0xE58D7000, 0xEBFC41A8, 0xE3A02000, 0xE2850040, 0xE1A01002, 0xEBFC08EE, 0xEEB00A48, 0xE2850F56\n"
        ".word 0xE2863020, 0xE3A02000, 0xE3A01023, 0xE58D7000, 0xEBFC419D, 0xE2850F56, 0xE3A02000, 0xE3A01001\n"
        ".word 0xEBFC08E3, 0xE2844001, 0xE3540002, 0xBAFFFFE3, 0xE5D80000, 0xE2800001, 0xE5C80000, 0xE28DD020\n"
        ".word 0xECBD8B02, 0xE8BD81F0, 0x0043D9E0, 0x3F800000, 0x00000339, 0x535C3A63, 0x5C34544D, 0x36445258\n"
        ".word 0x735C3638, 0x34736464, 0x6F72705C, 0x6D617267, 0x6269625C, 0x625C656C, 0x656C6269, 0x6967654C\n"
        ".word 0x72446E6F, 0x632E7761, 0x00007070, 0x00000474, 0x00000000, 0xC0400000, 0x003AC6A0, 0x6967654C\n"
        ".word 0x72446E6F, 0x70557761, 0x4C414320, 0x00000043, 0x00402450\n"
    );
}
// DECOMP_FUNC(0x003c9ebc, 664)


// Exact ARMv6K body recovered from 0x003C9EBC. The C++ reference documents
// the roster counting, allocation, population, sorting, and tail-state reset.
__attribute__((naked)) void UniteCtrl_func_003c9ebc(UniteCtrlRoster*) {
    asm volatile(
        ".word 0xE92D43F0, 0xE1A05000, 0xE3A01000, 0xE24DD044, 0xE1A00001, 0xEBFBDBFB, 0xE1A04000, 0xEBFBDBEF\n"
        ".word 0xE1A00004, 0xEBFBDBD9, 0xE3A08000, 0xE58D8008, 0xE58D800C, 0xE58D8010, 0xE58D8014, 0xE58D8018\n"
        ".word 0xE58D801C, 0xE58D8020, 0xE58D8024, 0xE58D8028, 0xE58D802C, 0xE58D8030, 0xE58D8034, 0xE58D8038\n"
        ".word 0xE58D803C, 0xE5858000, 0xE5858004, 0xE5858008, 0xE585800C, 0xE5858010, 0xE5858014, 0xE5858018\n"
        ".word 0xE585801C, 0xE5858020, 0xE5858024, 0xE5858028, 0xE585802C, 0xE1A06000, 0xE5858030, 0xE3560000\n"
        ".word 0xE3A04000, 0xE5858034, 0x9A00000D, 0xE6FF0074, 0xEBFBBCFC, 0xE5D01002, 0xE3510038, 0x2A000005\n"
        ".word 0xE1D000B6, 0xE3100001, 0x0A000002, 0xE7D50001, 0xE2800001, 0xE7C50001, 0xE2844001, 0xE1540006\n"
        ".word 0x3AFFFFF1, 0xE3A04000, 0xE3A09001, 0xE0857104, 0xE5878038, 0xE7D50004, 0xE3500000, 0x0A00000A\n"
        ".word 0xE3A010D5, 0xE28F0F53, 0xE1A00000, 0xE58D9000, 0xE7D50004, 0xE3A01C01, 0xE3A02000, 0xE1A03100\n"
        ".word 0xE1A00001, 0xEBFBEAE7, 0xE5870038, 0xE2844001, 0xE3540038, 0xBAFFFFEC, 0xE3560000, 0xE3A04000\n"
        ".word 0x828D7008, 0x83A09002, 0x9A00001B, 0xE6FF0074, 0xEBFBBCD4, 0xE5D01002, 0xE3510038, 0x2A000013\n"
        ".word 0xE1D020B6, 0xE3120001, 0x0A000010, 0xE0853101, 0xE7D71001, 0xE5933038, 0xE1D020B0, 0xE0831101\n"
        ".word 0xE1C120B0, 0xE5D01002, 0xE5D02003, 0xE7D7C001, 0xE0853101, 0xE5931038, 0xE089310C, 0xE18120B3\n"
        ".word 0xE5D00002, 0xE7D71000, 0xE2811001, 0xE7C71000, 0xE2844001, 0xE1540006, 0x3AFFFFE3, 0xE1A06005\n"
        ".word 0xE3A04000, 0xE3A07038, 0xE0850104, 0xE5900038, 0xE3500000, 0x0A000003, 0xE5D61000, 0xE59F30B0\n"
        ".word 0xE3A02004, 0xFBFBB798, 0xE2577001, 0xE2866001, 0xE2844001, 0x1AFFFFF3, 0xE2850C01, 0xE5C5811C\n"
        ".word 0xE1C081BE, 0xE5C58118, 0xE1C081BA, 0xE5C58143, 0xE5C58120, 0xE5C58121, 0xE5858122, 0xE5858126\n"
        ".word 0xE585812A, 0xE585812E, 0xE5C58132, 0xE1D023B4, 0xE3E01000, 0xE3C22B3F, 0xE1C023B4, 0xE5C58136\n"
        ".word 0xE1C013B8, 0xE1C013BA, 0xE5C5817C, 0xE28DD044, 0xE1A00005, 0xE8BD83F0, 0x535C3A63, 0x5C34544D\n"
        ".word 0x36445258, 0x735C3638, 0x34736464, 0x6F72705C, 0x6D617267, 0x6D61675C, 0x74616465, 0x6E755C61\n"
        ".word 0x5C657469, 0x74696E55, 0x72744365, 0x70632E6C, 0x00000070, 0x00219600\n"
    );
}
// DECOMP_FUNC(0x0022d5c8, 892)


// Exact ARMv6K body recovered from 0x0022D5C8. The C++ reference documents
// the Legion-roster and ordinary compendium paths and their shared UI tail.
__attribute__((naked)) void unite_func_0022d5c8(UniteExtrasWork*) {
    asm volatile(
        ".word 0xE92D4FF0, 0xE1A05000, 0xE24DD034, 0xE280BE59, 0xE5900590, 0xEB001901, 0xE2850B01, 0xE2800F57\n"
        ".word 0xE58D000C, 0xEB0018EE, 0xE5D515A4, 0xE2850B01, 0xE2800F6A, 0xE3510001, 0xE2859C05, 0xE285ACA5\n"
        ".word 0xE58D0008, 0x0A00006B, 0xEB00039E, 0xE59F8320, 0xE3A07000, 0xE1A04007, 0xE2840001, 0xE6FF0070\n"
        ".word 0xEB022F4D, 0xE1B06000, 0xE320F000, 0x0A00001A, 0xE1D600B6, 0xE3100001, 0x0A000017, 0xE1D600B0\n"
        ".word 0xE2877001, 0xEB01C5AD, 0xE3500000, 0xE320F000, 0x0A000011, 0xE1D610B0, 0xE3A02000, 0xE28D0010\n"
        ".word 0xEB000328, 0xE3A00000, 0xE58D0000, 0xE1D509D4, 0xE5D515A5, 0xE3A02000, 0xE3500064, 0xE1D600B0\n"
        ".word 0xA3A03001, 0xB3A03000, 0xEB01BE9A, 0xE58D0018, 0xE59D0008, 0xE28D1010, 0xEB000311, 0xE2844001\n"
        ".word 0xE1580004, 0xCAFFFFDB, 0xE1CA7ABE, 0xE1D90AB8, 0xE3500000, 0x0A000018, 0xEB01CE39, 0xE5F0100F\n"
        ".word 0xE201207F, 0xE3520001, 0x03A01006, 0x0A00000C, 0xE3520002, 0x03A01004, 0x0A000009, 0xE3520003\n"
        ".word 0x03A01016, 0x0A000006, 0xE3520007, 0x03A01018, 0x0A000003, 0xE3C1207F, 0xE3822001, 0xE3A01006\n"
        ".word 0xE5C02000, 0xE5D00000, 0xE3100080, 0x12810001, 0x16AF1070, 0xE59D0008, 0xEB0002DA, 0xE3A04001\n"
        ".word 0xE58D4000, 0xE58D4004, 0xE1D92AF8, 0xE3A03000, 0xE3A0100A, 0xE2850020, 0xEB00185F, 0xE3A01001\n"
        ".word 0xE2850020, 0xE1A00000, 0xE5C5402D, 0xE59D0008, 0xEB0002B9, 0xE5C50094, 0xE3A00000, 0xEB026034\n"
        ".word 0xE5950590, 0xE5901000, 0xE5912008, 0xE2851020, 0xE12FFF32, 0xE59B0000, 0xE59F21B8, 0xE1F010B4\n"
        ".word 0xE3811A01, 0xE1C010B0, 0xE5953028, 0xE59D000C, 0xE3A0101D, 0xE353000A, 0xA3A0300A, 0xEB001816\n"
        ".word 0xE3A00001, 0xE5C5056C, 0xE28DD034, 0xE3A00000, 0xE8BD4FF0, 0xEA02601E, 0xE320F000, 0xEB000331\n"
        ".word 0xE320F000, 0xE320F000, 0xEB01EC8C, 0xE2808A09, 0xE1A06000, 0xE5D8010B, 0xE3A04000, 0xE3500000\n"
        ".word 0x9A000027, 0xE0860004, 0xE2800A09, 0xE1D00FD0, 0xE3500000, 0xBA00001D, 0xE0801380, 0xE0810400\n"
        ".word 0xE0860100, 0xE2800090, 0xE1A07000, 0xEB027EAC, 0xE3500000, 0xE320F000, 0x1A000014, 0xE1D704B6\n"
        ".word 0xEB022ECD, 0xE1D010B0, 0xE1A07000, 0xE3A02001, 0xE28D0010, 0xEB0002B3, 0xE3A00000, 0xE58D0000\n"
        ".word 0xE1D509D4, 0xE5D515A5, 0xE3A02000, 0xE3500064, 0xE1D700B0, 0xA3A03001, 0xB3A03000, 0xEB01BE25\n"
        ".word 0xE58D0018, 0xE59D0008, 0xE28D1010, 0xEB00029C, 0xE5D8010B, 0xE2841001, 0xE6FF4071, 0xE1500004\n"
        ".word 0x8AFFFFD7, 0xE3A00018, 0xE1CA0ABE, 0xE3A04001, 0xE58D4000, 0xE58D4004, 0xE1D92AF8, 0xE3A03000\n"
        ".word 0xE3A0100A, 0xE2850020, 0xEB001803, 0xE3A01001, 0xE2850020, 0xE1A00000, 0xE59F8074, 0xE3A07000\n"
        ".word 0xE5C5402D, 0xE1A06007, 0xE1A04007, 0xE2840001, 0xE6FF0070, 0xEB022EA0, 0xE3500000, 0xE320F000\n"
        ".word 0x0A000007, 0xE1D010B6, 0xE3110001, 0x0A000004, 0xE1D000B0, 0xE2866001, 0xEB01C500, 0xE3500000\n"
        ".word 0x12877001, 0xE2844001, 0xE1540008, 0xBAFFFFEE, 0xE1A01006, 0xE1A00007, 0xEB05FFE6, 0xE5C50094\n"
        ".word 0xE3A00000, 0xEB025FC2, 0xE320F000, 0xE320F000, 0xEAFFFF8A, 0x000004FF, 0x0000040E\n"
    );
}

} // namespace smt4::camp
