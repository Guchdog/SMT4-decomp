#include "camp/unite_extras.h"
#include "engine/asd_symbols.h"
#include "ui/tbb_table.h"

#include <bit>
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

    // 0x002B9364 (140 B): 0x94-byte table row lookup by u16 id.  The battle
    // and UI TUs spell the same address Battle_GetTalkEntry/Item_GetTableEntry.
    const UniteBibleRow* camp_func_002b9364(u32 id);

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

    // 0x002C3344 (40 B): zero 0x20 bytes.
    void  camp_func_002c3344(void* block);

    // 0x002C32F8 (76 B): text block init.  The 5th..11th arguments are the
    // stack words at 0x003AD45C: 0x18, 0.0f, 0, 0.0f, 0, 0x00402450, 0x70.
    void  camp_func_002c32f8(void* object, u32 a1, u32 a2, u32 a3, u32 a4,
                             f32 f4, u32 a6, f32 f6, u32 a8, f32 f8, u32 a10);

    // 0x002BDB2C (152 B): reset + initialise one 0x8C-byte sprite node.
    void  camp_func_002bdb2c(void* sprite, u32 a1, u32 a2, void* a3, f32 scale,
                             u32 a5);

    // 0x002AF854 (64 B): attach a table row to a sprite node.
    void  battle_func_002af854(void* sprite, u32 a1, u32 a2);

    // 0x002C0BCC (56 B): LCG draw over [0, range].
    u32   engine_func_002c0bcc(u32 range);

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

// DECOMP_FUNC(0x0022d5c8, 892)
void unite_func_0022d5c8(UniteExtrasWork* work) {
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
                camp_func_002b9364(record->demon_id);                     // 0x0022D828
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
            const UniteBibleRow* row = camp_func_002b9364(static_cast<u16>(i + 1));         // 0x0022D8DC
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
            const UniteBibleRow* row = camp_func_002b9364(static_cast<u16>(i + 1));         // 0x0022D628
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

// DECOMP_FUNC(0x003a7ad8, 668)
void bibleDevil_func_003a7ad8(UniteExtrasWork* work) {
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

// DECOMP_FUNC(0x003ab770, 592)
void bibleLegionSkill_func_003ab770(UniteExtrasWork* work) {
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

// DECOMP_FUNC(0x003ad300, 596)
void bibleLegionDraw_func_003ad300() {
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
        work->field_288 = static_cast<u16>(engine_func_002c0bcc(0xC8) + 0x64); // 0x003AD3B8
        work->field_278 = 0.0f;                                           // 0x003AD3C4 (s17)
        work->field_280 = -3.0f;                                          // 0x003AD3C8 (0xC0400000)
        work->field_286 = 0;                                              // 0x003AD3D0
        work->field_28a = static_cast<u16>(engine_func_002c0bcc(0xC8) + 0x64); // 0x003AD3DC
        work->field_28c = 0;                                              // 0x003AD3C0
        work->field_28d = 0;                                              // 0x003AD3E8
        AsdMem_Zero(work->block_290, 0x1E0);                              // 0x003AD3EC
        work->field_470 = 0;                                              // 0x003AD378
    }

    work->calc_task = AsdTask_CreateCalc(
        "LegionDrawUp CALC", 2, 0, 0,
        TaskCallback(0x003ac6a0), 0, 0);                                  // 0x003AD410
    camp_func_002c3344(At(work, 0x20));                                   // 0x003AD41C
    camp_func_002c32f8(
        At(work, 0x20), 0x00402414, 0x24, 0x00402438,
        0x18, 0.0f, 0, 0.0f, 0,
        std::bit_cast<f32>(0x00402450u), 0x70);                           // 0x003AD454

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

// DECOMP_FUNC(0x003c9ebc, 664)
void UniteCtrl_func_003c9ebc(UniteCtrlRoster* roster) {
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
        const UniteBibleRow* row = camp_func_002b9364(static_cast<u16>(i));
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
            const UniteBibleRow* row = camp_func_002b9364(static_cast<u16>(i));
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

} // namespace smt4::camp
