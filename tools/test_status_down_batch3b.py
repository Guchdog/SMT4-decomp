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
#include "ui/status.h"
#include <cstring>

using namespace smt4::ui;

extern void* g_CampMessageBundle;

extern "C" {
void Sound_PlaySE(s32 se_id);
const void* Msg_GetCommonArchive(u32 archive_id);
const void* Msg_GetEntryFromBundle(const void* bundle, s32 msg_index);
void AsdText_SetMessageSource(void* text_handle, u32 mode, s32 mask, u32 a3, u32 a4, const void* msg_data, s32 id);
s32 AsdText_GetLineCount(void* text_handle);
void UiListCursor_Setup(void* cursor, s32 total_items, s32 visible_rows, s32 cols, s32 wrap_row, s32 repeat);
void UiListCursor_ResetScroll(void* cursor, s32 pos);
void AsdMem_Copy(void* dst, const void* src, u32 size);
bool Category_IsUnlocked(u16 category_id);
bool Category_HasItems(u32 category_id);
void Camp_SetSubHeaderMode(u32 mode);
void UiAnimSprite_SetAnim(void* sprite, s32 anim_idx, s32 mode);
s32 Category_GetVisibleRowLimit();
void UiListCursor_SetSelectedRow(void* cursor, s32 row);
}

namespace smt4::ui {

void StatusDown_UpdateHelpMessage(s32 msg_index) {
    auto* work = g_StatusDownWork;
    if (work->active_sound_id < 0 && msg_index >= 0 && work->active_mode == 1) {
        const s32 menu_id = Status_GetMainMenuId();
        s32 se_id = 0x2B;
        if (menu_id == 0xD || menu_id == 6) {
            se_id = 0x31;
        } else if (menu_id == 8 || menu_id == 9 || menu_id == 0xB || menu_id == 7) {
            se_id = 0x60;
        } else if (menu_id == 2) {
            se_id = 0x27;
        }
        Sound_PlaySE(se_id);
    }

    work->active_sound_id = static_cast<s16>(msg_index);
    if (msg_index < 0) {
        const void* common_arc = Msg_GetCommonArchive(0x40);
        AsdText_SetMessageSource(work->text_handle, 3, -1, 0, 3, common_arc, 0);
    } else {
        const void* entry = Msg_GetEntryFromBundle(g_CampMessageBundle, msg_index);
        if (entry == nullptr) {
            entry = Msg_GetCommonArchive(0x40);
        }
        AsdText_SetMessageSource(work->text_handle, 3, -1, 0, 3, entry, msg_index);
    }

    const s32 line_count = AsdText_GetLineCount(work->text_handle);
    UiListCursor_Setup(&work->list_cursor_help, line_count, 8, 1, 0, 1);
    UiListCursor_ResetScroll(&work->list_cursor_help, 0);
    work->needs_refresh = 1;
}

void StatusDown_UpdatePartySlotsAndDiff(const u16* ids, s32 count) {
    auto* work = g_StatusDownWork;
    u16 prev_ids[8];
    for (s32 i = 0; i < 8; ++i) {
        prev_ids[i] = work->party_ids[i];
    }
    for (s32 i = 0; i < 4; ++i) {
        reinterpret_cast<u32*>(work->new_party_flags)[i] = 0;
        reinterpret_cast<u32*>(work->party_ids)[i] = 0;
    }
    AsdMem_Copy(work->party_ids, ids, static_cast<u32>(count << 1));

    s32 valid_count = 0;
    while (valid_count < count && work->party_ids[valid_count] != 0) {
        ++valid_count;
    }

    UiListCursor_Setup(&work->list_cursor_main, valid_count, 8, 1, 0, 1);
    work->needs_refresh = 1;
    work->flag_548 = 0;

    for (s32 i = 0; i < count; ++i) {
        const u16 cur_id = work->party_ids[i];
        if (cur_id == 0) {
            continue;
        }
        s32 j = 0;
        for (; j < 8; ++j) {
            if (prev_ids[j] != 0 && prev_ids[j] == cur_id) {
                break;
            }
        }
        if (j >= 8) {
            work->new_party_flags[i] = 1;
        }
    }
}

void StatusDown_OpenCategorySelect(u16 arg0, u8 flag_413) {
    auto* work = g_StatusDownWork;
    work->category_arg0 = arg0;
    work->flag_413 = flag_413;
    for (s32 i = 0; i < 4; ++i) {
        reinterpret_cast<u32*>(work->category_ids)[i] = 0;
    }

    s32 matched_count = 0;
    for (u32 id = 0x79F; id <= 0x802; ++id) {
        if (id == 0) {
            id = 1;
        }
        if (Category_IsUnlocked(static_cast<u16>(id)) && Category_HasItems(id)) {
            work->category_ids[matched_count++] = static_cast<u16>(id);
        }
    }

    Camp_SetSubHeaderMode(0xE);
    Sound_PlaySE(5);
    UiAnimSprite_SetAnim(&work->panel_sprites[0], 1, 0);

    if (Category_GetVisibleRowLimit() <= matched_count) {
        const s32 rows = Category_GetVisibleRowLimit() + 1;
        UiListCursor_Setup(&work->category_cursor, rows, 9, 1, 1, 1);
        work->sub_state = 0x19;
    } else {
        const s32 rows = Category_GetVisibleRowLimit();
        UiListCursor_Setup(&work->category_cursor, rows, 9, 1, 1, 1);
        UiListCursor_SetSelectedRow(&work->category_cursor, matched_count);
        work->sub_state = 0x16;
    }

    auto* w = g_StatusDownWork;
    w->state_timer = 0;
    const u32 old_state = w->state;
    w->state = 1;
    w->prev_state = old_state;
}

}
"""

build_dir = Path("build/test_status_down_batch3b")
build_dir.mkdir(parents=True, exist_ok=True)
src_file = build_dir / "test.cpp"
obj_file = build_dir / "test.o"
src_file.write_text(test_cpp, encoding="utf-8")

res = compile_tu_armv6k(src_file, obj_file, repo_root=Path('.'))
assert res.returncode == 0, f"Compilation failed: {res.stderr}"
dec_funcs = extract_elf_functions_detailed(obj_file)
print("Compiled 3 StatusDown batch 3b functions successfully.")

def get_elf_section(path, target_name):
    data = Path(path).read_bytes()
    e_shoff, e_shentsize, e_shnum, e_shstrndx = struct.unpack_from("<IIHH", data, 32)[0], struct.unpack_from("<H", data, 46)[0], struct.unpack_from("<H", data, 48)[0], struct.unpack_from("<H", data, 50)[0]
    sections = [struct.unpack_from("<IIIIIIIIII", data, e_shoff + i * e_shentsize) for i in range(e_shnum)]
    shstr = sections[e_shstrndx]
    shstrtab = data[shstr[4] : shstr[4] + shstr[5]]
    for s in sections:
        end = shstrtab.find(b"\x00", s[0])
        name = shstrtab[s[0]:end].decode("ascii", errors="replace")
        if name == target_name:
            return data[s[4]:s[4]+s[5]]
    return b""

rodata_data = get_elf_section(obj_file, ".rodata")
print(f"rodata size: {len(rodata_data)}")

STUB_BASE = 0x02000000
RET_ADDR = 0x03000000
GLOBAL_PTR_ADDR = 0x0044E190
BUNDLE_PTR_ADDR = 0x00433158
WORK_STRUCT_ADDR = 0x02100000
NEW_SLOTS_ADDR = 0x02200000
RODATA_ADDR = 0x02300000

STUB_MAP = {
    '_ZN4smt42ui20Status_GetMainMenuIdEv': STUB_BASE + 0x00,
    'Sound_PlaySE': STUB_BASE + 0x10,
    'Msg_GetCommonArchive': STUB_BASE + 0x20,
    'Msg_GetEntryFromBundle': STUB_BASE + 0x30,
    'AsdText_SetMessageSource': STUB_BASE + 0x40,
    'AsdText_GetLineCount': STUB_BASE + 0x50,
    'UiListCursor_Setup': STUB_BASE + 0x60,
    'UiListCursor_ResetScroll': STUB_BASE + 0x70,
    'AsdMem_Copy': STUB_BASE + 0x80,
    'Category_IsUnlocked': STUB_BASE + 0x90,
    'Category_HasItems': STUB_BASE + 0xA0,
    'Camp_SetSubHeaderMode': STUB_BASE + 0xB0,
    'UiAnimSprite_SetAnim': STUB_BASE + 0xC0,
    'Category_GetVisibleRowLimit': STUB_BASE + 0xD0,
    'UiListCursor_SetSelectedRow': STUB_BASE + 0xE0,
    '_ZN4smt42ui16g_StatusDownWorkE': GLOBAL_PTR_ADDR,
    'g_CampMessageBundle': BUNDLE_PTR_ADDR,
    '': RODATA_ADDR,
}

ORIG_ADDR_MAP = {
    0x0029af30: '_ZN4smt42ui20Status_GetMainMenuIdEv',
    0x002b8b78: 'Sound_PlaySE',
    0x002b49d8: 'Msg_GetCommonArchive',
    0x00389294: 'Msg_GetEntryFromBundle',
    0x00296d8c: 'AsdText_SetMessageSource',
    0x002b787c: 'AsdText_GetLineCount',
    0x0029fae8: 'UiListCursor_Setup',
    0x0020fe24: 'UiListCursor_ResetScroll',
    0x002c5ff4: 'AsdMem_Copy',
    0x00262edc: 'Category_IsUnlocked',
    0x002890d0: 'Category_HasItems',
    0x002a0ea8: 'Camp_SetSubHeaderMode',
    0x002bdac0: 'UiAnimSprite_SetAnim',
    0x0026ace0: 'Category_GetVisibleRowLimit',
    0x0029edfc: 'UiListCursor_SetSelectedRow',
}

ARITY = {
    '_ZN4smt42ui20Status_GetMainMenuIdEv': 0,
    'Sound_PlaySE': 1,
    'Msg_GetCommonArchive': 1,
    'Msg_GetEntryFromBundle': 2,
    'AsdText_SetMessageSource': 7,
    'AsdText_GetLineCount': 1,
    'UiListCursor_Setup': 6,
    'UiListCursor_ResetScroll': 2,
    'AsdMem_Copy': 3,
    'Category_IsUnlocked': 1,
    'Category_HasItems': 1,
    'Camp_SetSubHeaderMode': 1,
    'UiAnimSprite_SetAnim': 3,
    'Category_GetVisibleRowLimit': 0,
    'UiListCursor_SetSelectedRow': 2,
}

def apply_relocs(code_bytes, relocs, target_addr):
    mutable = bytearray(code_bytes)
    for rel in relocs:
        offset = rel.offset
        name = rel.symbol_name
        rel_type = rel.relocation_type
        if name in STUB_MAP:
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
        if user_data == '_ZN4smt42ui20Status_GetMainMenuIdEv':
            uc.reg_write(UC_ARM_REG_R0, 2)
        elif user_data == 'Msg_GetCommonArchive':
            uc.reg_write(UC_ARM_REG_R0, 0x02150000)
        elif user_data == 'Msg_GetEntryFromBundle':
            uc.reg_write(UC_ARM_REG_R0, 0x02160000)
        elif user_data == 'AsdText_GetLineCount':
            uc.reg_write(UC_ARM_REG_R0, 3)
        elif user_data == 'Category_IsUnlocked':
            uc.reg_write(UC_ARM_REG_R0, 1)
        elif user_data == 'Category_HasItems':
            cat_id = uc.reg_read(UC_ARM_REG_R0)
            uc.reg_write(UC_ARM_REG_R0, 1 if cat_id in (0x79F, 0x7A0) else 0)
        elif user_data == 'Category_GetVisibleRowLimit':
            uc.reg_write(UC_ARM_REG_R0, 5)
        elif user_data == 'AsdMem_Copy':
            dst = uc.reg_read(UC_ARM_REG_R0)
            src = uc.reg_read(UC_ARM_REG_R1)
            sz = uc.reg_read(UC_ARM_REG_R2)
            data = uc.mem_read(src, sz)
            uc.mem_write(dst, bytes(data))
            
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
    (0x002cf4e0, '_ZN4smt42ui28StatusDown_UpdateHelpMessageEi', {'r0': 5}, 352),
    (0x002e2f44, '_ZN4smt42ui34StatusDown_UpdatePartySlotsAndDiffEPKti', {'r0': NEW_SLOTS_ADDR, 'r1': 4}, 408),
    (0x00311494, '_ZN4smt42ui29StatusDown_OpenCategorySelectEth', {'r0': 0x1234, 'r1': 1}, 356),
]

for orig_addr, func_name, reg_inits, func_size in TARGETS:
    print(f"\nTesting {func_name} (0x{orig_addr:x})...")
    
    # 1. Orig
    uc_orig = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc_orig.mem_map(0x00100000, 0x00500000, UC_PROT_READ | UC_PROT_WRITE | UC_PROT_EXEC)
    uc_orig.mem_map(0x0FFFF000, 0x00010000, UC_PROT_READ | UC_PROT_WRITE)
    uc_orig.mem_map(WORK_STRUCT_ADDR, 0x00010000, UC_PROT_READ | UC_PROT_WRITE)
    uc_orig.mem_map(NEW_SLOTS_ADDR, 0x00010000, UC_PROT_READ | UC_PROT_WRITE)
    uc_orig.mem_map(RET_ADDR, 0x00010000, UC_PROT_READ | UC_PROT_WRITE | UC_PROT_EXEC)
    uc_orig.mem_write(RET_ADDR, b"\x1e\xff\x2f\xe1")
    uc_orig.mem_write(0x00100000, ORIG_DATA)
    
    # Init work struct
    work_bytes = bytearray(0x4000)
    work_bytes[0x3fc] = 1 # active_mode = 1
    struct.pack_into('<h', work_bytes, 0x47e, -1) # active_sound_id = -1
    struct.pack_into('<I', work_bytes, 0x22a0, 0x02140000) # text_handle
    # previous party ids: [100, 101, 102, 0, 0, 0, 0, 0]
    struct.pack_into('<8H', work_bytes, 0x482, 100, 101, 102, 0, 0, 0, 0, 0)
    uc_orig.mem_write(WORK_STRUCT_ADDR, bytes(work_bytes))
    uc_orig.mem_write(GLOBAL_PTR_ADDR, struct.pack('<I', WORK_STRUCT_ADDR))
    uc_orig.mem_write(BUNDLE_PTR_ADDR, struct.pack('<I', 0x02170000))
    
    # New slots: [101, 103, 104, 0, 0, 0, 0, 0]
    new_slots = struct.pack('<8H', 101, 103, 104, 0, 0, 0, 0, 0)
    uc_orig.mem_write(NEW_SLOTS_ADDR, new_slots)
    
    tracker_orig = CallTracker()
    for addr, name in ORIG_ADDR_MAP.items():
        if addr != orig_addr:
            uc_orig.mem_write(addr, b"\x1e\xff\x2f\xe1")
            uc_orig.hook_add(unicorn.UC_HOOK_CODE, tracker_orig.hook_call, user_data=name, begin=addr, end=addr)
        
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
    uc_orig.emu_start(orig_addr, RET_ADDR, timeout=1000000)
    
    # 2. Dec
    dec_code = dec_funcs[func_name][0]
    relocs = dec_funcs[func_name][1]
    target_addr = 0x00380000
    patched_code = apply_relocs(dec_code, relocs, target_addr)
    
    uc_dec = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc_dec.mem_map(0x00100000, 0x00500000, UC_PROT_READ | UC_PROT_WRITE | UC_PROT_EXEC)
    uc_dec.mem_map(0x0FFFF000, 0x00010000, UC_PROT_READ | UC_PROT_WRITE)
    uc_dec.mem_map(WORK_STRUCT_ADDR, 0x00010000, UC_PROT_READ | UC_PROT_WRITE)
    uc_dec.mem_map(NEW_SLOTS_ADDR, 0x00010000, UC_PROT_READ | UC_PROT_WRITE)
    uc_dec.mem_map(STUB_BASE, 0x10000, UC_PROT_READ | UC_PROT_WRITE | UC_PROT_EXEC)
    uc_dec.mem_map(RET_ADDR, 0x10000, UC_PROT_READ | UC_PROT_WRITE | UC_PROT_EXEC)
    uc_dec.mem_map(RODATA_ADDR, 0x10000, UC_PROT_READ | UC_PROT_WRITE)
    if rodata_data:
        uc_dec.mem_write(RODATA_ADDR, rodata_data)
    uc_dec.mem_write(RET_ADDR, b"\x1e\xff\x2f\xe1")
    uc_dec.mem_write(0x00100000, ORIG_DATA)
    uc_dec.mem_write(target_addr, patched_code)
    
    uc_dec.mem_write(WORK_STRUCT_ADDR, bytes(work_bytes))
    uc_dec.mem_write(GLOBAL_PTR_ADDR, struct.pack('<I', WORK_STRUCT_ADDR))
    uc_dec.mem_write(BUNDLE_PTR_ADDR, struct.pack('<I', 0x02170000))
    uc_dec.mem_write(NEW_SLOTS_ADDR, new_slots)
    
    tracker_dec = CallTracker()
    for name, addr in STUB_MAP.items():
        if name not in ('_ZN4smt42ui16g_StatusDownWorkE', 'g_CampMessageBundle', ''):
            uc_dec.mem_write(addr, b"\x1e\xff\x2f\xe1")
            uc_dec.hook_add(unicorn.UC_HOOK_CODE, tracker_dec.hook_call, user_data=name, begin=addr, end=addr)
        
    uc_dec.reg_write(UC_ARM_REG_SP, 0x0FFFF000 + 0x8000)
    uc_dec.reg_write(UC_ARM_REG_LR, RET_ADDR)
    for r_name, r_val in reg_inits.items():
        reg_id = getattr(unicorn.arm_const, f"UC_ARM_REG_{r_name.upper()}")
        uc_dec.reg_write(reg_id, r_val)
    uc_dec.emu_start(target_addr, RET_ADDR, timeout=1000000)
    
    assert tracker_orig.calls == tracker_dec.calls, f"Calls mismatch for {func_name}:\n  Orig: {tracker_orig.calls}\n  Dec:  {tracker_dec.calls}"
    print(f"  Calls match: {tracker_dec.calls}")
    
    mem_orig = uc_orig.mem_read(WORK_STRUCT_ADDR, 0x2400)
    mem_dec = uc_dec.mem_read(WORK_STRUCT_ADDR, 0x2400)
    assert mem_orig == mem_dec, f"Work struct memory mismatch for {func_name}!"
    print(f"  Work struct memory matches 100%!")

print("\nALL 3 STATUSDOWN BATCH 3B FUNCTIONS MATCH 100%!")
