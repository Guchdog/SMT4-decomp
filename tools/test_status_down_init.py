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

static inline u32 SpriteTableWord(const void* pointer) {
    return static_cast<u32>(reinterpret_cast<std::uintptr_t>(pointer));
}

extern "C" {
    extern const u8 g_StatusDownSpriteTable[];
    void* AsdMem_Alloc(u32 align, u32 line, u32 zero_flag, u32 size, u32 flag);
    void  AsdMem_Zero(void* ptr, u32 size);
    void* AsdTask_CreateCalc(const char* name, u32 prio, u32 a2, u32 a3,
                             void (*cb)(void*), u32 a5, u32 a6);
    void* AsdTask_CreateDraw(const char* name, u32 prio, u32 a2, u32 a3,
                             void (*cb)(void*), u32 a5, u32 a6, void* parent);
    void  UiSpriteGroup_Init(void* group);
    void  UiSpriteGroup_BindTable(void* group, u32 a1, u32 a2, u32 a3,
                                 u32 a4, u32 a5, u32 a6, u32 a7, u32 a8,
                                 u32 a9, u32 a10);
    void  UiAnimSprite_Setup(UiAnimSprite* sprite, u32 res_group_id, s32 idx,
                             void* sprite_group, u32 flag, f32 scale);
    void  UiAnimSprite_SetupEx(UiAnimSprite* sprite, u32 res_group_id, s32 idx,
                               u32 sub_id, void* sprite_group, u32 a5, f32 scale);
    void  UiAnimSprite_SetAnim(UiAnimSprite* sprite, s32 anim_idx, s32 mode);
    void  UiAnimSprite_SetLayer(UiAnimSprite* sprite, s32 layer);
    void* AsdText_CreateDefault(u32 arg0);
    void  AsdText_SetAlpha(void* text_handle, u32 alpha);
    void  AsdText_SetColorAndScale(void* text_handle, u32 a1, u32 rgba, f32 scale);
    void  camp_func_002c4450(void* ptr, u32 size, s32 val) asm("camp_func_002c4450");
    void  StatusDown_CalcTaskCallback(void*);
    void  StatusDown_DrawTaskCallback(void*);
}

namespace smt4::ui {

void StatusDown_Init() {
    StatusDownWork* work = g_StatusDownWork;
    if (work == nullptr) {
        work = static_cast<StatusDownWork*>(
            AsdMem_Alloc(0x100, 0x100, 0, sizeof(StatusDownWork), 1));
        g_StatusDownWork = work;
    }

    AsdMem_Zero(work, sizeof(StatusDownWork));

    work->calc_task = AsdTask_CreateCalc("TMD CALC", 2, 0, 0,
                                         StatusDown_CalcTaskCallback, 0, 0);
    work->draw_task = AsdTask_CreateDraw("TMD DDRAW", 0xE7, 0, 0,
                                         StatusDown_DrawTaskCallback, 0, 0, work->calc_task);

    UiSpriteGroup_Init(&work->sprite_group);
    UiSpriteGroup_BindTable(&work->sprite_group,
                            SpriteTableWord(g_StatusDownSpriteTable - 0xA8), 0x48,
                            SpriteTableWord(g_StatusDownSpriteTable - 0x60), 0x48,
                            SpriteTableWord(g_StatusDownSpriteTable - 0x18),
                            0x18, 0, 0,
                            SpriteTableWord(g_StatusDownSpriteTable), 0x134);

    UiAnimSprite_Setup(&work->panel_sprites[0], 0x1A, 0x3E8, &work->sprite_group, 1, 1.0f);
    UiAnimSprite_SetAnim(&work->panel_sprites[0], 0, 0);

    UiAnimSprite_Setup(&work->panel_sprites[1], 0x1A, 0x3E8, &work->sprite_group, 1, 1.0f);
    UiAnimSprite_SetLayer(&work->panel_sprites[1], 0);

    UiAnimSprite_Setup(&work->panel_sprites[2], 0x1A, 0x3E8, &work->sprite_group, 1, 1.0f);
    UiAnimSprite_SetLayer(&work->panel_sprites[2], 1);

    UiAnimSprite_Setup(&work->panel_sprites[3], 0x1A, 0x3E8, &work->sprite_group, 1, 1.0f);
    UiAnimSprite_SetAnim(&work->panel_sprites[3], 4, 0);

    UiAnimSprite_Setup(&work->panel_sprites[4], 0x1A, 0x3E8, &work->sprite_group, 1, 1.0f);
    UiAnimSprite_SetAnim(&work->panel_sprites[4], 5, 0);

    UiAnimSprite_Setup(&work->panel_sprites[5], 0x1A, 0x3E8, &work->sprite_group, 1, 1.0f);
    UiAnimSprite_SetAnim(&work->panel_sprites[5], 0, 0);

    UiAnimSprite_SetupEx(&work->panel_sprites[6], 0x1A, -1, 0x1C, &work->sprite_group, 0xC9, 1.0f);
    UiAnimSprite_SetLayer(&work->panel_sprites[6], 2);
    *reinterpret_cast<u16*>(&work->panel_sprites[6].raw[0x3A]) = 2;

    work->text_handle = AsdText_CreateDefault(0);
    AsdText_SetAlpha(work->text_handle, 0xFF);
    AsdText_SetColorAndScale(work->text_handle, 0, 0x646464FFu, 0.0f);

    camp_func_002c4450(work->slot_touch_handles, 0x29, -1);
    work->visibility_flag = 1;
}

}
"""

build_dir = Path("build/test_status_down_init")
build_dir.mkdir(parents=True, exist_ok=True)
src_file = build_dir / "test.cpp"
obj_file = build_dir / "test.o"
src_file.write_text(test_cpp, encoding="utf-8")

res = compile_tu_armv6k(src_file, obj_file, repo_root=Path('.'))
assert res.returncode == 0, f"Compilation failed: {res.stderr}"
dec_funcs = extract_elf_functions_detailed(obj_file)
print("Compiled StatusDown_Init successfully.")

STUB_BASE = 0x02000000
RET_ADDR = 0x03000000
GLOBAL_PTR_ADDR = 0x0044E190
WORK_STRUCT_ADDR = 0x02100000
SPRITE_TABLE_ADDR = 0x00407D58
RODATA_ADDR = 0x02300000

STUB_MAP = {
    'AsdMem_Alloc': STUB_BASE + 0x00,
    'AsdMem_Zero': STUB_BASE + 0x10,
    'AsdTask_CreateCalc': STUB_BASE + 0x20,
    'AsdTask_CreateDraw': STUB_BASE + 0x30,
    'UiSpriteGroup_Init': STUB_BASE + 0x40,
    'UiSpriteGroup_BindTable': STUB_BASE + 0x50,
    'UiAnimSprite_Setup': STUB_BASE + 0x60,
    'UiAnimSprite_SetAnim': STUB_BASE + 0x70,
    'UiAnimSprite_SetLayer': STUB_BASE + 0x80,
    'UiAnimSprite_SetupEx': STUB_BASE + 0x90,
    'AsdText_CreateDefault': STUB_BASE + 0xA0,
    'AsdText_SetAlpha': STUB_BASE + 0xB0,
    'AsdText_SetColorAndScale': STUB_BASE + 0xC0,
    'camp_func_002c4450': STUB_BASE + 0xD0,
    '_ZN4smt42ui27StatusDown_CalcTaskCallbackEPv': 0x001ca648,
    '_ZN4smt42ui27StatusDown_DrawTaskCallbackEPv': 0x001cc914,
    '_ZN4smt42ui16g_StatusDownWorkE': GLOBAL_PTR_ADDR,
    'g_StatusDownSpriteTable': SPRITE_TABLE_ADDR,
    '': RODATA_ADDR,
}

ORIG_ADDR_MAP = {
    0x002c4b84: 'AsdMem_Alloc',
    0x002c4b30: 'AsdMem_Zero',
    0x002c5978: 'AsdTask_CreateCalc',
    0x002c4c00: 'AsdTask_CreateDraw',
    0x002c3344: 'UiSpriteGroup_Init',
    0x002c32f8: 'UiSpriteGroup_BindTable',
    0x002bdb2c: 'UiAnimSprite_Setup',
    0x002bdac0: 'UiAnimSprite_SetAnim',
    0x002bf030: 'UiAnimSprite_SetLayer',
    0x002bf0a8: 'UiAnimSprite_SetupEx',
    0x002bda1c: 'AsdText_CreateDefault',
    0x002bda10: 'AsdText_SetAlpha',
    0x002bda00: 'AsdText_SetColorAndScale',
    0x002c4450: 'camp_func_002c4450',
}

ARITY = {
    'AsdMem_Alloc': 4,
    'AsdMem_Zero': 2,
    'AsdTask_CreateCalc': 4,
    'AsdTask_CreateDraw': 4,
    'UiSpriteGroup_Init': 1,
    'UiSpriteGroup_BindTable': 4,
    'UiAnimSprite_Setup': 4,
    'UiAnimSprite_SetAnim': 3,
    'UiAnimSprite_SetLayer': 2,
    'UiAnimSprite_SetupEx': 4,
    'AsdText_CreateDefault': 1,
    'AsdText_SetAlpha': 2,
    'AsdText_SetColorAndScale': 4,
    'camp_func_002c4450': 3,
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
        if user_data in ('AsdTask_CreateCalc', 'AsdTask_CreateDraw'):
            str_ptr = uc.reg_read(UC_ARM_REG_R0)
            str_val = bytes(uc.mem_read(str_ptr, 10)).split(b'\x00')[0].decode('ascii')
            self.calls.append((user_data, (str_val,) + tuple(regs[1:arity])))
        else:
            self.calls.append((user_data, tuple(regs[:arity])))
        
        # Stubs return values:
        if user_data == 'AsdMem_Alloc':
            uc.reg_write(UC_ARM_REG_R0, WORK_STRUCT_ADDR)
        elif user_data == 'AsdTask_CreateCalc':
            uc.reg_write(UC_ARM_REG_R0, 0x02110000)
        elif user_data == 'AsdTask_CreateDraw':
            uc.reg_write(UC_ARM_REG_R0, 0x02120000)
        elif user_data == 'AsdText_CreateDefault':
            uc.reg_write(UC_ARM_REG_R0, 0x02130000)
        elif user_data == 'camp_func_002c4450':
            ptr = uc.reg_read(UC_ARM_REG_R0)
            sz = uc.reg_read(UC_ARM_REG_R1)
            val = uc.reg_read(UC_ARM_REG_R2) & 0xFF
            uc.mem_write(ptr, bytes([val] * sz))
            
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

def get_elf_section(path, target_name):
    data = Path(path).read_bytes()
    e_shoff, e_shentsize, e_shnum, e_shstrndx = struct.unpack_from("<IIHH", data, 32)[0], struct.unpack_from("<H", data, 46)[0], struct.unpack_from("<H", data, 48)[0], struct.unpack_from("<H", data, 50)[0]
    sections = [struct.unpack_from("<IIIIIIIIII", data, e_shoff + i * e_shentsize) for i in range(e_shnum)]
    shstr = sections[e_shstrndx]
    shstrtab = data[shstr[4] : shstr[4] + shstr[5]]
    for s in sections:
        end = shstrtab.find(b"\x00", s[0])
        name = shstrtab[s[0]:end].decode("ascii", errors="replace")
        if name == target_name or name.startswith(target_name):
            return data[s[4]:s[4]+s[5]]
    return b""

rodata_data = get_elf_section(obj_file, ".rodata")

for test_case, init_work_ptr in [("work_is_null", 0), ("work_is_set", WORK_STRUCT_ADDR)]:
    print(f"\\n--- Running StatusDown_Init test case: {test_case} ---")
    orig_addr = 0x002d931c
    func_name = '_ZN4smt42ui15StatusDown_InitEv'
    
    # 1. Orig
    uc_orig = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc_orig.ctl_set_cpu_model(unicorn.arm_const.UC_CPU_ARM_11MPCORE)
    uc_orig.reg_write(UC_ARM_REG_C1_C0_2, 0x00F00000)
    uc_orig.reg_write(UC_ARM_REG_FPEXC, 0x40000000)
    uc_orig.mem_map(0x00100000, 0x00500000, UC_PROT_READ | UC_PROT_WRITE | UC_PROT_EXEC)
    uc_orig.mem_map(0x0FFFF000, 0x00010000, UC_PROT_READ | UC_PROT_WRITE)
    uc_orig.mem_map(WORK_STRUCT_ADDR, 0x00010000, UC_PROT_READ | UC_PROT_WRITE)
    uc_orig.mem_map(RET_ADDR, 0x00010000, UC_PROT_READ | UC_PROT_WRITE | UC_PROT_EXEC)
    uc_orig.mem_write(RET_ADDR, b"\\x1e\\xff\\x2f\\xe1")
    uc_orig.mem_write(0x00100000, ORIG_DATA)
    uc_orig.mem_write(GLOBAL_PTR_ADDR, struct.pack('<I', init_work_ptr))
    
    tracker_orig = CallTracker()
    def hook_unmapped_orig(uc, access, address, size, value, user_data):
        pc = uc.reg_read(UC_ARM_REG_PC)
        lr = uc.reg_read(UC_ARM_REG_LR)
        print(f"[{func_name}] Orig unmapped at PC=0x{pc:x}, LR=0x{lr:x}, addr=0x{address:x}")
        return False
    uc_orig.hook_add(unicorn.UC_HOOK_MEM_READ_UNMAPPED | unicorn.UC_HOOK_MEM_WRITE_UNMAPPED | unicorn.UC_HOOK_MEM_FETCH_UNMAPPED, hook_unmapped_orig)

    def hook_code_debug(uc, address, size, user_data):
        pass
    def hook_invalid(uc, user_data):
        pc = uc.reg_read(UC_ARM_REG_PC)
        print(f"Invalid insn at PC=0x{pc:x}")
    uc_orig.hook_add(unicorn.UC_HOOK_INSN_INVALID, hook_invalid)
    for addr, name in ORIG_ADDR_MAP.items():
        if addr != orig_addr:
            uc_orig.mem_write(addr, b"\\x1e\\xff\\x2f\\xe1")
            uc_orig.hook_add(unicorn.UC_HOOK_CODE, tracker_orig.hook_call, user_data=name, begin=addr, end=addr)
        
    uc_orig.reg_write(UC_ARM_REG_SP, 0x0FFFF000 + 0x8000)
    uc_orig.reg_write(UC_ARM_REG_LR, RET_ADDR)
    uc_orig.emu_start(orig_addr, RET_ADDR, timeout=1000000)
    
    # 2. Dec
    dec_code = dec_funcs[func_name][0]
    relocs = dec_funcs[func_name][1]
    target_addr = 0x00380000
    patched_code = apply_relocs(dec_code, relocs, target_addr)
    
    uc_dec = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc_dec.ctl_set_cpu_model(unicorn.arm_const.UC_CPU_ARM_11MPCORE)
    uc_dec.reg_write(UC_ARM_REG_C1_C0_2, 0x00F00000)
    uc_dec.reg_write(UC_ARM_REG_FPEXC, 0x40000000)
    uc_dec.mem_map(0x00100000, 0x00500000, UC_PROT_READ | UC_PROT_WRITE | UC_PROT_EXEC)
    uc_dec.mem_map(0x0FFFF000, 0x00010000, UC_PROT_READ | UC_PROT_WRITE)
    uc_dec.mem_map(WORK_STRUCT_ADDR, 0x00010000, UC_PROT_READ | UC_PROT_WRITE)
    uc_dec.mem_map(STUB_BASE, 0x10000, UC_PROT_READ | UC_PROT_WRITE | UC_PROT_EXEC)
    uc_dec.mem_map(RET_ADDR, 0x10000, UC_PROT_READ | UC_PROT_WRITE | UC_PROT_EXEC)
    uc_dec.mem_map(RODATA_ADDR, 0x10000, UC_PROT_READ | UC_PROT_WRITE)
    if rodata_data:
        uc_dec.mem_write(RODATA_ADDR, rodata_data)
    uc_dec.mem_write(RET_ADDR, b"\\x1e\\xff\\x2f\\xe1")
    uc_dec.mem_write(0x00100000, ORIG_DATA)
    uc_dec.mem_write(target_addr, patched_code)
    uc_dec.mem_write(GLOBAL_PTR_ADDR, struct.pack('<I', init_work_ptr))
    
    tracker_dec = CallTracker()
    for name, addr in STUB_MAP.items():
        if name not in ('_ZN4smt42ui16g_StatusDownWorkE', 'g_StatusDownSpriteTable', '_ZN4smt42ui27StatusDown_CalcTaskCallbackEPv', '_ZN4smt42ui27StatusDown_DrawTaskCallbackEPv', ''):
            uc_dec.mem_write(addr, b"\\x1e\\xff\\x2f\\xe1")
            uc_dec.hook_add(unicorn.UC_HOOK_CODE, tracker_dec.hook_call, user_data=name, begin=addr, end=addr)
        
    uc_dec.reg_write(UC_ARM_REG_SP, 0x0FFFF000 + 0x8000)
    uc_dec.reg_write(UC_ARM_REG_LR, RET_ADDR)
    uc_dec.emu_start(target_addr, RET_ADDR, timeout=1000000)
    
    assert tracker_orig.calls == tracker_dec.calls, f"Calls mismatch for {func_name}:\\n  Orig: {tracker_orig.calls}\\n  Dec:  {tracker_dec.calls}"
    print(f"  Calls match: {len(tracker_dec.calls)} calls!")
    
    mem_orig = uc_orig.mem_read(WORK_STRUCT_ADDR, 0x2400)
    mem_dec = uc_dec.mem_read(WORK_STRUCT_ADDR, 0x2400)
    assert mem_orig == mem_dec, f"Work struct memory mismatch for {func_name}!"
    print(f"  Work struct memory matches 100%!")
    
    glob_orig = uc_orig.mem_read(GLOBAL_PTR_ADDR, 4)
    glob_dec = uc_dec.mem_read(GLOBAL_PTR_ADDR, 4)
    assert glob_orig == glob_dec, f"Global ptr memory mismatch for {func_name}!"
    print(f"  Global ptr matches: {hex(struct.unpack('<I', glob_dec)[0])}")

print("\\nSTATUSDOWN_INIT MATCHES 100% ACROSS ALL CASES!")
