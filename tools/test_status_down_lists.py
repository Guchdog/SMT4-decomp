import sys
import struct
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import unicorn
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_ARM, UC_PROT_READ, UC_PROT_WRITE, UC_PROT_EXEC
from unicorn.arm_const import *
from tools.build_check import compile_tu_armv6k
from tools.asm_diff import extract_elf_functions_detailed

CODE_PATH = Path("extracted/exefs/code.bin")
ORIG_DATA = CODE_PATH.read_bytes()

test_cpp = """
#include "types.h"
#include "ui/status_down.h"
#include <cstring>

using namespace smt4::ui;

struct ItemTableEntry {
    u16 id;          // +0x00
    u8  category;    // +0x02
    u8  rarity;      // +0x03
    u16 unk_04;      // +0x04
    u16 flags;       // +0x06
    u8  unk_08[0x30];// +0x08..+0x38
    u16 skill_id;    // +0x38
};

extern "C" {
void AsdMem_Zero(void* ptr, u32 size);
void* camp_func_002b9364(u32 id);
void UiListCursor_Setup(void* cursor, s32 total_items, s32 visible_rows, s32 cols, s32 wrap_row, s32 repeat);
void UiListCursor_SetSelectedRow(void* cursor, s32 row);
void UiListCursor_SetSelectedCol(void* cursor, s32 col);
const u8* Camp_GetSortConfig();
void qsort_arm(void* base, s32 nmemb, u32 size, s32 (*compar)(const void*, const void*));

s32 StatusDown_SkillSortByIdDesc(const void*, const void*);
s32 StatusDown_SkillSortByIdAsc(const void*, const void*);
s32 StatusDown_SkillSortByCostDesc(const void*, const void*);
s32 StatusDown_SkillSortByCostAsc(const void*, const void*);
s32 SkillSort_ByNameDesc(const void*, const void*);
s32 StatusDown_SkillSortByNameAsc(const void*, const void*);

s32 StatusDown_ItemSortByIdDesc(const void*, const void*);
s32 StatusDown_ItemSortByIdAsc(const void*, const void*);
s32 StatusDown_ItemSortByTypeDesc(const void*, const void*);
s32 StatusDown_ItemSortByTypeAsc(const void*, const void*);
s32 ItemSort_ByCountDesc(const void*, const void*);
s32 ItemSort_ByCountAsc(const void*, const void*);
s32 ItemSort_ByNameDesc(const void*, const void*);
s32 ItemSort_ByNameAsc(const void*, const void*);
}

namespace smt4::ui {
void StatusDown_SortItemList();

void StatusDown_PopulateSkillList(const u8* skill_bitfield) {
    auto* work = g_StatusDownWork;
    work->skill_count = 0;
    work->skill_total = 0;
    AsdMem_Zero(work->skill_entries, sizeof(work->skill_entries));

    for (u16 i = 0; i < 0x500; ++i) {
        const auto* entry = static_cast<const ItemTableEntry*>(camp_func_002b9364(i));
        if (entry == nullptr) {
            continue;
        }
        if ((entry->flags & 1) == 0 || entry->skill_id == 0) {
            continue;
        }
        const u16 sid = entry->skill_id;
        if ((skill_bitfield[sid >> 3] & (1u << (sid & 7))) != 0) {
            const s16 idx = work->skill_count;
            work->skill_entries[idx].id = entry->id;
            work->skill_entries[idx].value = entry->skill_id;
            work->skill_count = static_cast<s16>(idx + 1);
        }
        work->skill_total = static_cast<s16>(work->skill_total + 1);
    }

    UiListCursor_Setup(&work->skill_cursor, work->skill_count, 11, 1, 0, 1);

    auto* w = g_StatusDownWork;
    const u8* sort_cfg = Camp_GetSortConfig();
    const u8 skill_sort = sort_cfg[0x15];
    const u8 sort_key = skill_sort & 0x7F;
    const bool desc = (skill_sort >> 7) != 0;

    if (sort_key == 1) {
        qsort_arm(w->skill_entries, w->skill_count, sizeof(StatusDownListEntry),
                  desc ? StatusDown_SkillSortByIdDesc : StatusDown_SkillSortByIdAsc);
    } else if (sort_key == 0x21) {
        qsort_arm(w->skill_entries, w->skill_count, sizeof(StatusDownListEntry),
                  desc ? StatusDown_SkillSortByCostDesc : StatusDown_SkillSortByCostAsc);
    } else if (sort_key == 3) {
        qsort_arm(w->skill_entries, w->skill_count, sizeof(StatusDownListEntry),
                  desc ? SkillSort_ByNameDesc : StatusDown_SkillSortByNameAsc);
    }

    work->needs_refresh = 1;
}

void StatusDown_PopulateItemList(const u8* item_counts) {
    auto* work = g_StatusDownWork;
    work->item_count = 0;
    work->item_nonzero_count = 0;
    AsdMem_Zero(work->item_entries, sizeof(work->item_entries));

    for (u16 i = 0; i < 0x500; ++i) {
        const auto* entry = static_cast<const ItemTableEntry*>(camp_func_002b9364(i));
        if (entry == nullptr || (entry->flags & 1) == 0) {
            continue;
        }
        const u16 item_id = entry->id;
        const u8 qty = item_counts[item_id];
        if (qty == 0) {
            continue;
        }
        const s16 idx = work->item_count;
        work->item_entries[idx].id = item_id;
        work->item_entries[idx].value = qty;
        if (qty != 0) {
            work->item_nonzero_count = static_cast<s16>(work->item_nonzero_count + 1);
        }
        work->item_count = static_cast<s16>(idx + 1);
    }

    UiListCursor_Setup(&work->item_cursor, work->item_count, 9, 4, 1, 1);

    if (work->item_count > 0 &&
        work->item_count <= (work->item_saved_col + (work->item_saved_row << 2))) {
        const s16 new_row = static_cast<s16>((work->item_count - 1) / 4);
        const s16 new_col = static_cast<s16>((work->item_count - 1) - (new_row << 2));
        work->item_saved_row = new_row;
        work->item_saved_col = new_col;
        UiListCursor_SetSelectedRow(&work->item_cursor, new_row);
        UiListCursor_SetSelectedCol(&work->item_cursor, work->item_saved_col);
    } else {
        UiListCursor_SetSelectedRow(&work->item_cursor, work->item_saved_row);
        UiListCursor_SetSelectedCol(&work->item_cursor, work->item_saved_col);
    }

    StatusDown_SortItemList();
    work->needs_refresh = 1;
}

void StatusDown_SortItemList() {
    auto* work = g_StatusDownWork;
    const u8* sort_cfg = Camp_GetSortConfig();
    const u8 item_sort = sort_cfg[0x16];
    const u8 sort_key = item_sort & 0x7F;
    const bool desc = (item_sort >> 7) != 0;

    if (sort_key == 1) {
        qsort_arm(work->item_entries, work->item_count, sizeof(StatusDownListEntry),
                  desc ? StatusDown_ItemSortByIdDesc : StatusDown_ItemSortByIdAsc);
    } else if (sort_key == 8) {
        qsort_arm(work->item_entries, work->item_count, sizeof(StatusDownListEntry),
                  desc ? StatusDown_ItemSortByTypeDesc : StatusDown_ItemSortByTypeAsc);
    } else if (sort_key == 2) {
        qsort_arm(work->item_entries, work->item_count, sizeof(StatusDownListEntry),
                  desc ? ItemSort_ByCountDesc : ItemSort_ByCountAsc);
    } else if (sort_key == 3) {
        qsort_arm(work->item_entries, work->item_count, sizeof(StatusDownListEntry),
                  desc ? ItemSort_ByNameDesc : ItemSort_ByNameAsc);
    }
}

}
"""

build_dir = Path("build/test_status_down_lists")
build_dir.mkdir(parents=True, exist_ok=True)
src_file = build_dir / "test.cpp"
obj_file = build_dir / "test.o"
src_file.write_text(test_cpp, encoding="utf-8")

res = compile_tu_armv6k(src_file, obj_file, repo_root=Path('.'))
assert res.returncode == 0, f"Compilation failed: {res.stderr}"
dec_funcs = extract_elf_functions_detailed(obj_file)
print("Compiled 3 StatusDown list functions successfully.")

STUB_BASE = 0x02000000
RET_ADDR = 0x03000000
GLOBAL_PTR_ADDR = 0x0044E190
WORK_STRUCT_ADDR = 0x02100000
BITFIELD_ADDR = 0x02200000
ITEM_COUNTS_ADDR = 0x02201000
SORT_CFG_ADDR = 0x02202000
ITEM_ENTRY_TABLE_ADDR = 0x02210000

STUB_MAP = {
    'AsdMem_Zero': STUB_BASE + 0x00,
    'camp_func_002b9364': STUB_BASE + 0x10,
    'UiListCursor_Setup': STUB_BASE + 0x20,
    'UiListCursor_SetSelectedRow': STUB_BASE + 0x30,
    'UiListCursor_SetSelectedCol': STUB_BASE + 0x40,
    'Camp_GetSortConfig': STUB_BASE + 0x50,
    'qsort_arm': STUB_BASE + 0x60,
    '_ZN4smt42ui28StatusDown_SkillSortByIdDescEPKvS2_': 0x002e4534,
    '_ZN4smt42ui27StatusDown_SkillSortByIdAscEPKvS2_': 0x00206be8,
    '_ZN4smt42ui30StatusDown_SkillSortByCostDescEPKvS2_': 0x002dc96c,
    '_ZN4smt42ui29StatusDown_SkillSortByCostAscEPKvS2_': 0x001f60dc,
    'SkillSort_ByNameDesc': 0x002dca04,
    '_ZN4smt42ui29StatusDown_SkillSortByNameAscEPKvS2_': 0x001f6174,
    '_ZN4smt42ui27StatusDown_ItemSortByIdDescEPKvS2_': 0x002e4608,
    '_ZN4smt42ui26StatusDown_ItemSortByIdAscEPKvS2_': 0x00206cbc,
    '_ZN4smt42ui29StatusDown_ItemSortByTypeDescEPKvS2_': 0x002e4584,
    '_ZN4smt42ui28StatusDown_ItemSortByTypeAscEPKvS2_': 0x00206c38,
    'ItemSort_ByCountDesc': 0x002c6d30,
    'ItemSort_ByCountAsc': 0x001d1bb8,
    'ItemSort_ByNameDesc': 0x002dca98,
    'ItemSort_ByNameAsc': 0x001f61a4,
    '_ZN4smt42ui23StatusDown_SortItemListEv': STUB_BASE + 0x70,
    '_ZN4smt42ui16g_StatusDownWorkE': GLOBAL_PTR_ADDR,
}

ORIG_ADDR_MAP = {
    0x002c4b30: 'AsdMem_Zero',
    0x002b9364: 'camp_func_002b9364',
    0x0029fae8: 'UiListCursor_Setup',
    0x0029edfc: 'UiListCursor_SetSelectedRow',
    0x0029eb58: 'UiListCursor_SetSelectedCol',
    0x002a0fac: 'Camp_GetSortConfig',
    0x002b7f08: 'qsort_arm',
    0x002b7f0a: 'qsort_arm',
    0x0027f3d4: 'qsort_arm',
    0x0032c4bc: '_ZN4smt42ui23StatusDown_SortItemListEv',
}

ARITY = {
    'AsdMem_Zero': 2,
    'camp_func_002b9364': 1,
    'UiListCursor_Setup': 6,
    'UiListCursor_SetSelectedRow': 2,
    'UiListCursor_SetSelectedCol': 2,
    'Camp_GetSortConfig': 0,
    'qsort_arm': 4,
    '_ZN4smt42ui23StatusDown_SortItemListEv': 0,
}

def apply_relocs(code_bytes, relocs, target_addr, text_offset=0):
    mutable = bytearray(code_bytes)
    for rel in relocs:
        offset = rel.offset
        name = rel.symbol_name
        rel_type = rel.relocation_type
        if name == '':
            sym_val = target_addr - text_offset
        elif name in STUB_MAP:
            sym_val = STUB_MAP[name]
        else:
            raise ValueError(f"Unknown symbol '{name}'")
            
        if rel_type in (28, 29): # R_ARM_CALL / R_ARM_JUMP24
            orig = struct.unpack_from('<I', mutable, offset)[0]
            target = sym_val
            pc = target_addr + offset + 8
            new_disp = ((target - pc) >> 2) & 0x00FFFFFF
            inst = (orig & 0xFF000000) | new_disp
            struct.pack_into('<I', mutable, offset, inst)
        elif rel_type in (2, 38): # R_ARM_ABS32 or R_ARM_TARGET1
            orig = struct.unpack_from('<I', mutable, offset)[0]
            val = (sym_val + orig) & 0xFFFFFFFF
            struct.pack_into('<I', mutable, offset, val)
        else:
            raise ValueError(f"Unsupported reloc type {rel_type}")
    return bytes(mutable)

class CallTracker:
    def __init__(self):
        self.calls = []
        
    def hook_call(self, uc, address, size, user_data):
        regs = [
            hex(uc.reg_read(UC_ARM_REG_R0)),
            hex(uc.reg_read(UC_ARM_REG_R1)),
            hex(uc.reg_read(UC_ARM_REG_R2)),
            hex(uc.reg_read(UC_ARM_REG_R3)),
        ]
        arity = ARITY.get(user_data, 4)
        self.calls.append((user_data, tuple(regs[:arity])))
        
        # Stubs return values:
        if user_data == 'camp_func_002b9364':
            idx = uc.reg_read(UC_ARM_REG_R0)
            if idx < 0x500:
                uc.reg_write(UC_ARM_REG_R0, ITEM_ENTRY_TABLE_ADDR + idx * 0x40)
            else:
                uc.reg_write(UC_ARM_REG_R0, 0)
        elif user_data == 'Camp_GetSortConfig':
            uc.reg_write(UC_ARM_REG_R0, SORT_CFG_ADDR)
        elif user_data == 'AsdMem_Zero':
            dst = uc.reg_read(UC_ARM_REG_R0)
            sz = uc.reg_read(UC_ARM_REG_R1)
            uc.mem_write(dst, b'\x00' * sz)
            
        lr = uc.reg_read(UC_ARM_REG_LR)
        if lr == 0:
            uc.emu_stop()
            return
        if lr & 1:
            uc.reg_write(UC_ARM_REG_CPSR, uc.reg_read(UC_ARM_REG_CPSR) | 0x20)
            uc.reg_write(UC_ARM_REG_PC, lr & ~1)
        else:
            uc.reg_write(UC_ARM_REG_CPSR, uc.reg_read(UC_ARM_REG_CPSR) & ~0x20)
            uc.reg_write(UC_ARM_REG_PC, lr)

TARGETS = [
    (0x001ee5a4, '_ZN4smt42ui28StatusDown_PopulateSkillListEPKh', {'r0': BITFIELD_ADDR}, 548),
    (0x001ee7c8, '_ZN4smt42ui27StatusDown_PopulateItemListEPKh', {'r0': ITEM_COUNTS_ADDR}, 384),
    (0x0032c4bc, '_ZN4smt42ui23StatusDown_SortItemListEv', {}, 372),
]

for orig_addr, func_name, reg_inits, func_size in TARGETS:
    print(f"\nTesting {func_name} (0x{orig_addr:x})...")
    
    # 1. Orig
    uc_orig = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc_orig.mem_map(0x00100000, 0x00500000, UC_PROT_READ | UC_PROT_WRITE | UC_PROT_EXEC)
    uc_orig.mem_map(0x0FFFF000, 0x00010000, UC_PROT_READ | UC_PROT_WRITE)
    uc_orig.mem_map(WORK_STRUCT_ADDR, 0x00010000, UC_PROT_READ | UC_PROT_WRITE)
    uc_orig.mem_map(BITFIELD_ADDR, 0x00010000, UC_PROT_READ | UC_PROT_WRITE)
    uc_orig.mem_map(ITEM_ENTRY_TABLE_ADDR, 0x00020000, UC_PROT_READ | UC_PROT_WRITE)
    uc_orig.mem_map(RET_ADDR, 0x00010000, UC_PROT_READ | UC_PROT_WRITE | UC_PROT_EXEC)
    uc_orig.mem_write(RET_ADDR, b"\x1e\xff\x2f\xe1")
    uc_orig.mem_write(0x00100000, ORIG_DATA)
    
    # Init work struct
    work_bytes = bytearray(0x4000)
    struct.pack_into('<h', work_bytes, 0x2234, 1) # item_saved_col = 1
    struct.pack_into('<h', work_bytes, 0x2236, 0) # item_saved_row = 0
    uc_orig.mem_write(WORK_STRUCT_ADDR, bytes(work_bytes))
    uc_orig.mem_write(GLOBAL_PTR_ADDR, struct.pack('<I', WORK_STRUCT_ADDR))
    
    # Init bitfield with some bits set (skills 1, 2, 8)
    bitfield_bytes = bytearray(0x100)
    bitfield_bytes[0] = 0x06 # bits 1 and 2
    bitfield_bytes[1] = 0x01 # bit 8
    uc_orig.mem_write(BITFIELD_ADDR, bytes(bitfield_bytes))
    
    # Init item counts (items 1: 5, 2: 10)
    item_counts = bytearray(0x500)
    item_counts[1] = 5
    item_counts[2] = 10
    uc_orig.mem_write(ITEM_COUNTS_ADDR, bytes(item_counts))
    
    # Init sort config: byte 0x15 = 1 (sort by id asc), byte 0x16 = 1 (sort by id asc)
    sort_cfg = bytearray(0x100)
    sort_cfg[0x15] = 1
    sort_cfg[0x16] = 1
    uc_orig.mem_write(SORT_CFG_ADDR, bytes(sort_cfg))
    
    # Init mock ItemTable entries for 0..0x500
    for i in range(0x500):
        entry_bytes = bytearray(0x40)
        struct.pack_into('<H', entry_bytes, 0x00, i) # id = i
        struct.pack_into('<H', entry_bytes, 0x06, 1 if i in (1, 2, 3) else 0) # flags bit 0
        struct.pack_into('<H', entry_bytes, 0x38, i if i in (1, 2) else 0) # skill_id
        uc_orig.mem_write(ITEM_ENTRY_TABLE_ADDR + i * 0x40, bytes(entry_bytes))
    
    tracker_orig = CallTracker()
    for addr, name in ORIG_ADDR_MAP.items():
        if addr != orig_addr:
            if addr & 1 or addr == 0x002b7f0a:
                uc_orig.mem_write(addr & ~1, b"\x70\x47\x00\x00")
            else:
                uc_orig.mem_write(addr, b"\x1e\xff\x2f\xe1")
            uc_orig.hook_add(unicorn.UC_HOOK_CODE, tracker_orig.hook_call, user_data=name, begin=addr & ~1, end=addr | 1)
        
    def hook_unmapped_orig(uc, access, address, size, value, user_data):
        pc = uc.reg_read(UC_ARM_REG_PC)
        lr = uc.reg_read(UC_ARM_REG_LR)
        print(f"[{func_name}] Orig unmapped at PC=0x{pc:x}, LR=0x{lr:x}, addr=0x{address:x}")
        return False
    uc_orig.hook_add(unicorn.UC_HOOK_MEM_READ_UNMAPPED | unicorn.UC_HOOK_MEM_WRITE_UNMAPPED | unicorn.UC_HOOK_MEM_FETCH_UNMAPPED, hook_unmapped_orig)
    
    uc_orig.reg_write(UC_ARM_REG_SP, 0x0FFFF000 + 0x8000)
    uc_orig.reg_write(UC_ARM_REG_LR, RET_ADDR)
    for r_name, r_val in reg_inits.items():
        reg_id = getattr(unicorn.arm_const, f"UC_ARM_REG_{r_name.upper()}")
        uc_orig.reg_write(reg_id, r_val)
    try:
        uc_orig.emu_start(orig_addr, RET_ADDR, timeout=1000000)
    except Exception as e:
        pc = uc_orig.reg_read(UC_ARM_REG_PC)
        lr = uc_orig.reg_read(UC_ARM_REG_LR)
        print(f"Orig exception {e} at PC=0x{pc:x}, LR=0x{lr:x}")
        raise
    
    # 2. Dec
    dec_code = dec_funcs[func_name][0]
    relocs = dec_funcs[func_name][1]
    target_addr = 0x00380000
    patched_code = apply_relocs(dec_code, relocs, target_addr, text_offset=0x2a4)
    
    uc_dec = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc_dec.mem_map(0x00100000, 0x00500000, UC_PROT_READ | UC_PROT_WRITE | UC_PROT_EXEC)
    uc_dec.mem_map(0x0FFFF000, 0x00010000, UC_PROT_READ | UC_PROT_WRITE)
    uc_dec.mem_map(WORK_STRUCT_ADDR, 0x00010000, UC_PROT_READ | UC_PROT_WRITE)
    uc_dec.mem_map(BITFIELD_ADDR, 0x00010000, UC_PROT_READ | UC_PROT_WRITE)
    uc_dec.mem_map(ITEM_ENTRY_TABLE_ADDR, 0x00020000, UC_PROT_READ | UC_PROT_WRITE)
    uc_dec.mem_map(STUB_BASE, 0x10000, UC_PROT_READ | UC_PROT_WRITE | UC_PROT_EXEC)
    uc_dec.mem_map(RET_ADDR, 0x10000, UC_PROT_READ | UC_PROT_WRITE | UC_PROT_EXEC)
    uc_dec.mem_write(RET_ADDR, b"\x1e\xff\x2f\xe1")
    uc_dec.mem_write(0x00100000, ORIG_DATA)
    uc_dec.mem_write(target_addr, patched_code)
    
    uc_dec.mem_write(WORK_STRUCT_ADDR, bytes(work_bytes))
    uc_dec.mem_write(GLOBAL_PTR_ADDR, struct.pack('<I', WORK_STRUCT_ADDR))
    uc_dec.mem_write(BITFIELD_ADDR, bytes(bitfield_bytes))
    uc_dec.mem_write(ITEM_COUNTS_ADDR, bytes(item_counts))
    uc_dec.mem_write(SORT_CFG_ADDR, bytes(sort_cfg))
    for i in range(0x500):
        entry_bytes = bytearray(0x40)
        struct.pack_into('<H', entry_bytes, 0x00, i)
        struct.pack_into('<H', entry_bytes, 0x06, 1 if i in (1, 2, 3) else 0)
        struct.pack_into('<H', entry_bytes, 0x38, i if i in (1, 2) else 0)
        uc_dec.mem_write(ITEM_ENTRY_TABLE_ADDR + i * 0x40, bytes(entry_bytes))
    
    tracker_dec = CallTracker()
    for name, addr in STUB_MAP.items():
        if name != '_ZN4smt42ui16g_StatusDownWorkE' and name not in (
            'StatusDown_SkillSortByIdDesc', 'StatusDown_SkillSortByIdAsc',
            'StatusDown_SkillSortByCostDesc', 'StatusDown_SkillSortByCostAsc',
            'SkillSort_ByNameDesc', 'StatusDown_SkillSortByNameAsc',
            'StatusDown_ItemSortByIdDesc', 'StatusDown_ItemSortByIdAsc',
            'StatusDown_ItemSortByTypeDesc', 'StatusDown_ItemSortByTypeAsc',
            'ItemSort_ByCountDesc', 'ItemSort_ByCountAsc',
            'ItemSort_ByNameDesc', 'ItemSort_ByNameAsc'
        ):
            uc_dec.mem_write(addr, b"\x1e\xff\x2f\xe1")
            uc_dec.hook_add(unicorn.UC_HOOK_CODE, tracker_dec.hook_call, user_data=name, begin=addr, end=addr)
        
    uc_dec.reg_write(UC_ARM_REG_SP, 0x0FFFF000 + 0x8000)
    uc_dec.reg_write(UC_ARM_REG_LR, RET_ADDR)
    for r_name, r_val in reg_inits.items():
        reg_id = getattr(unicorn.arm_const, f"UC_ARM_REG_{r_name.upper()}")
        uc_dec.reg_write(reg_id, r_val)
    uc_dec.emu_start(target_addr, RET_ADDR, timeout=1000000)
    
    # Filter out camp_func_002b9364 calls for cleaner comparison since both call it 0x500 times
    calls_orig_filtered = [c for c in tracker_orig.calls if c[0] != 'camp_func_002b9364']
    calls_dec_filtered = [c for c in tracker_dec.calls if c[0] != 'camp_func_002b9364']
    assert calls_orig_filtered == calls_dec_filtered, f"Calls mismatch for {func_name}:\n  Orig: {calls_orig_filtered}\n  Dec:  {calls_dec_filtered}"
    print(f"  Calls match: {calls_dec_filtered}")
    
    mem_orig = uc_orig.mem_read(WORK_STRUCT_ADDR, 0x2300)
    mem_dec = uc_dec.mem_read(WORK_STRUCT_ADDR, 0x2300)
    assert mem_orig == mem_dec, f"Work struct memory mismatch for {func_name}!"
    print(f"  Work struct memory matches 100%!")

print("\nALL 3 STATUSDOWN LIST FUNCTIONS MATCH 100%!")
