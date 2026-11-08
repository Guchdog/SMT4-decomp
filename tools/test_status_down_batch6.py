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

using namespace smt4::ui;

extern "C" {
bool Camp_CanShowLRPrompts();
void UiSprite_DrawNode(u32 screen, u32 group_id, u32 node_id, s32 x, s32 y, s32 prio);
}

namespace smt4::ui {

bool StatusDown_CanOpenSubScreen() {
    if (Status_GetSubMenuState() == 5 ||
        Status_GetSubMenuState() == 6 ||
        Status_GetSubMenuState() == 10 ||
        Status_GetMainMenuId() == 7 ||
        Status_GetMainMenuId() == 8 ||
        Status_GetMainMenuId() == 3) {
        return false;
    }
    return true;
}

void StatusDown_DrawLRPrompts(s32 x_offset, s32 y_offset) {
    auto* work = g_StatusDownWork;
    if (!Camp_CanShowLRPrompts()) {
        return;
    }
    u32 left = work->lr_state_left;
    if (left == 1 || left == 2) {
        UiSprite_DrawNode(2, 0x1A, 0x4D5, x_offset, y_offset, 0xBA);
        UiSprite_DrawNode(2, 0x1A, 0x4D9, x_offset, y_offset, 0xBA);
    } else {
        UiSprite_DrawNode(2, 0x1A, 0x4D3, x_offset, y_offset, 0xBA);
        UiSprite_DrawNode(2, 0x1A, 0x4D7, x_offset, y_offset, 0xBA);
    }
    u32 right = work->lr_state_right;
    if (right == 1 || right == 2) {
        UiSprite_DrawNode(2, 0x1A, 0x4D4, x_offset, y_offset, 0xBA);
        UiSprite_DrawNode(2, 0x1A, 0x4D8, x_offset, y_offset, 0xBA);
    } else {
        UiSprite_DrawNode(2, 0x1A, 0x4D2, x_offset, y_offset, 0xBA);
        UiSprite_DrawNode(2, 0x1A, 0x4D6, x_offset, y_offset, 0xBA);
    }
}

u8 StatusDown_GetActiveMode() {
    auto* work = g_StatusDownWork;
    return work->active_mode;
}

u32 StatusDown_GetField53C() {
    auto* work = g_StatusDownWork;
    return work->field_53c;
}

void StatusDown_SetFlag412(u8 val) {
    auto* work = g_StatusDownWork;
    if (work != nullptr) {
        work->flag_412 = val;
    }
}

void StatusDown_SetFlag411(u8 val) {
    auto* work = g_StatusDownWork;
    if (work != nullptr) {
        work->flag_411 = val;
    }
}

}
"""

build_dir = Path("build/test_status_down_batch6")
build_dir.mkdir(parents=True, exist_ok=True)
src_file = build_dir / "test.cpp"
obj_file = build_dir / "test.o"
src_file.write_text(test_cpp, encoding="utf-8")

res = compile_tu_armv6k(src_file, obj_file, repo_root=Path('.'))
assert res.returncode == 0, f"Compilation failed: {res.stderr}"
dec_funcs = extract_elf_functions_detailed(obj_file)
print("Compiled 6 StatusDown functions successfully.")

STUB_BASE = 0x02000000
RET_ADDR = 0x03000000
GLOBAL_PTR_ADDR = 0x0044E190
WORK_STRUCT_ADDR = 0x02100000

STUB_MAP = {
    '_ZN4smt42ui22Status_GetSubMenuStateEv': STUB_BASE + 0x00,
    '_ZN4smt42ui20Status_GetMainMenuIdEv': STUB_BASE + 0x10,
    'Camp_CanShowLRPrompts': STUB_BASE + 0x20,
    'UiSprite_DrawNode': STUB_BASE + 0x30,
    '_ZN4smt42ui16g_StatusDownWorkE': GLOBAL_PTR_ADDR,
}

ORIG_ADDR_MAP = {
    0x00288408: '_ZN4smt42ui22Status_GetSubMenuStateEv',
    0x0029af30: '_ZN4smt42ui20Status_GetMainMenuIdEv',
    0x00288700: 'Camp_CanShowLRPrompts',
    0x002bf460: 'UiSprite_DrawNode',
}

ARITY = {
    '_ZN4smt42ui22Status_GetSubMenuStateEv': 0,
    '_ZN4smt42ui20Status_GetMainMenuIdEv': 0,
    'Camp_CanShowLRPrompts': 0,
    'UiSprite_DrawNode': 6,
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
        if user_data == '_ZN4smt42ui22Status_GetSubMenuStateEv':
            uc.reg_write(UC_ARM_REG_R0, 1) # valid sub state
        elif user_data == '_ZN4smt42ui20Status_GetMainMenuIdEv':
            uc.reg_write(UC_ARM_REG_R0, 1) # valid main id
        elif user_data == 'Camp_CanShowLRPrompts':
            uc.reg_write(UC_ARM_REG_R0, 1) # can show LR prompts
            
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
    (0x00288718, '_ZN4smt42ui27StatusDown_CanOpenSubScreenEv', {}, 92),
    (0x0029adf0, '_ZN4smt42ui24StatusDown_DrawLRPromptsEii', {'r0': 10, 'r1': 20}, 320),
    (0x00293d50, '_ZN4smt42ui24StatusDown_GetActiveModeEv', {}, 20),
    (0x002956ac, '_ZN4smt42ui22StatusDown_GetField53CEv', {}, 20),
    (0x0029c6c4, '_ZN4smt42ui21StatusDown_SetFlag412Eh', {'r0': 1}, 24),
    (0x002efe8c, '_ZN4smt42ui21StatusDown_SetFlag411Eh', {'r0': 1}, 24),
]

for orig_addr, func_name, reg_inits, func_size in TARGETS:
    print(f"\nTesting {func_name} (0x{orig_addr:x})...")
    
    # 1. Orig
    uc_orig = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc_orig.mem_map(0x00100000, 0x00500000, UC_PROT_READ | UC_PROT_WRITE | UC_PROT_EXEC)
    uc_orig.mem_map(0x0FFFF000, 0x00010000, UC_PROT_READ | UC_PROT_WRITE)
    uc_orig.mem_map(WORK_STRUCT_ADDR, 0x00010000, UC_PROT_READ | UC_PROT_WRITE)
    uc_orig.mem_map(RET_ADDR, 0x00010000, UC_PROT_READ | UC_PROT_WRITE | UC_PROT_EXEC)
    uc_orig.mem_write(RET_ADDR, b"\x1e\xff\x2f\xe1")
    uc_orig.mem_write(0x00100000, ORIG_DATA)
    
    # Init work struct
    work_bytes = bytearray(0x4000)
    work_bytes[0x3fc] = 3 # active_mode = 3
    struct.pack_into('<I', work_bytes, 0x424, 1) # lr_state_left = 1
    struct.pack_into('<I', work_bytes, 0x428, 0) # lr_state_right = 0
    struct.pack_into('<I', work_bytes, 0x53c, 0x12345678) # field_53c
    uc_orig.mem_write(WORK_STRUCT_ADDR, bytes(work_bytes))
    uc_orig.mem_write(GLOBAL_PTR_ADDR, struct.pack('<I', WORK_STRUCT_ADDR))
    
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
    ret_orig = uc_orig.reg_read(UC_ARM_REG_R0)
    
    # 2. Dec
    dec_code = dec_funcs[func_name][0]
    relocs = dec_funcs[func_name][1]
    target_addr = 0x00380000
    patched_code = apply_relocs(dec_code, relocs, target_addr)
    
    uc_dec = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc_dec.mem_map(0x00100000, 0x00500000, UC_PROT_READ | UC_PROT_WRITE | UC_PROT_EXEC)
    uc_dec.mem_map(0x0FFFF000, 0x00010000, UC_PROT_READ | UC_PROT_WRITE)
    uc_dec.mem_map(WORK_STRUCT_ADDR, 0x00010000, UC_PROT_READ | UC_PROT_WRITE)
    uc_dec.mem_map(STUB_BASE, 0x10000, UC_PROT_READ | UC_PROT_WRITE | UC_PROT_EXEC)
    uc_dec.mem_map(RET_ADDR, 0x10000, UC_PROT_READ | UC_PROT_WRITE | UC_PROT_EXEC)
    uc_dec.mem_write(RET_ADDR, b"\x1e\xff\x2f\xe1")
    uc_dec.mem_write(0x00100000, ORIG_DATA)
    uc_dec.mem_write(target_addr, patched_code)
    
    uc_dec.mem_write(WORK_STRUCT_ADDR, bytes(work_bytes))
    uc_dec.mem_write(GLOBAL_PTR_ADDR, struct.pack('<I', WORK_STRUCT_ADDR))
    
    tracker_dec = CallTracker()
    for name, addr in STUB_MAP.items():
        if name != '_ZN4smt42ui16g_StatusDownWorkE':
            uc_dec.mem_write(addr, b"\x1e\xff\x2f\xe1")
            uc_dec.hook_add(unicorn.UC_HOOK_CODE, tracker_dec.hook_call, user_data=name, begin=addr, end=addr)
        
    uc_dec.reg_write(UC_ARM_REG_SP, 0x0FFFF000 + 0x8000)
    uc_dec.reg_write(UC_ARM_REG_LR, RET_ADDR)
    for r_name, r_val in reg_inits.items():
        reg_id = getattr(unicorn.arm_const, f"UC_ARM_REG_{r_name.upper()}")
        uc_dec.reg_write(reg_id, r_val)
    uc_dec.emu_start(target_addr, RET_ADDR, timeout=1000000)
    ret_dec = uc_dec.reg_read(UC_ARM_REG_R0)
    
    assert tracker_orig.calls == tracker_dec.calls, f"Calls mismatch for {func_name}:\n  Orig: {tracker_orig.calls}\n  Dec:  {tracker_dec.calls}"
    print(f"  Calls match: {tracker_dec.calls}")
    assert ret_orig == ret_dec, f"Return value mismatch for {func_name}: Orig {ret_orig} vs Dec {ret_dec}"
    print(f"  Return value matches: {hex(ret_dec)}")
    
    mem_orig = uc_orig.mem_read(WORK_STRUCT_ADDR, 0x600)
    mem_dec = uc_dec.mem_read(WORK_STRUCT_ADDR, 0x600)
    assert mem_orig == mem_dec, f"Work struct memory mismatch for {func_name}!"
    print(f"  Work struct memory matches 100%!")

print("\nALL 6 STATUSDOWN FUNCTIONS MATCH 100%!")
