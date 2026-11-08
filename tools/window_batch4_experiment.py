#!/usr/bin/env python3
"""
Differential test harness for Window Batch 4 functions in src/ui/window.cpp:
  - 0x0010b1b4: InfoWin_ShowMessage (172 B)
  - 0x0010b260: InfoWin_UpdateTimer (192 B)
  - 0x0010b510: GuestWin_HandlePrompt (104 B)
  - 0x0011b128: GuestWin_Calc (148 B)

Validates 100% semantic equivalence between original ARM binary and compiled C++.
"""

import struct
import sys
from pathlib import Path
import unicorn
from unicorn import (
    Uc, UC_ARCH_ARM, UC_MODE_ARM,
    UC_PROT_READ, UC_PROT_WRITE, UC_PROT_EXEC
)
from unicorn.arm_const import (
    UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3,
    UC_ARM_REG_SP, UC_ARM_REG_LR, UC_ARM_REG_PC,
)

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools.build_check import compile_tu_armv6k
from tools.asm_diff import extract_elf_functions_detailed

CODE_PATH = ROOT / "extracted" / "exefs" / "code.bin"
ORIG_DATA = CODE_PATH.read_bytes()
SOURCE = ROOT / "src" / "ui" / "window.cpp"

CODE_BASE = 0x00100000
CODE_SIZE = 0x00400000 # 4MB (spans 0x00100000 to 0x00500000)
STACK_BASE = 0x0FFFF000
STACK_SIZE = 0x00010000
STACK_TOP = STACK_BASE + STACK_SIZE - 0x100

STUB_BASE = 0x004B0000
STUB_MAP = {
    'ui_func_002c0ac8': STUB_BASE + 0x00,
    'func_002c00e8': STUB_BASE + 0x08,
    'UiGpu_BeginPass': STUB_BASE + 0x10,
    'func_002bfcb4': STUB_BASE + 0x18,
    'func_002bfc88': STUB_BASE + 0x20,
    'UiEngine_GetContext': STUB_BASE + 0x28,
    'engine_func_002c2b1c': STUB_BASE + 0x30,
    'battle_func_002b6e60': STUB_BASE + 0x38,
    'ui_func_002bf9f0': STUB_BASE + 0x40,
}

ORIG_ADDR_MAP = {
    0x002c0ac8: 'ui_func_002c0ac8',
    0x002c00e8: 'func_002c00e8',
    0x002c3ba8: 'UiGpu_BeginPass',
    0x002bfcb4: 'func_002bfcb4',
    0x002bfc88: 'func_002bfc88',
    0x002c2b1c: 'UiEngine_GetContext',
    0x002b6e60: 'battle_func_002b6e60',
    0x002bf9f0: 'ui_func_002bf9f0',
}

def create_emulator():
    uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc.mem_map(CODE_BASE, CODE_SIZE, UC_PROT_READ | UC_PROT_WRITE | UC_PROT_EXEC)
    uc.mem_map(STACK_BASE, STACK_SIZE, UC_PROT_READ | UC_PROT_WRITE)
    return uc

class StubTracker:
    def __init__(self, uc):
        self.uc = uc
        self.calls = []
        self.work_ptr = 0x00450000
        self.ctx_ptr = 0x00460000
        self.btl_ptr = 0x00470000
        self.func_002c00e8_ret = 0
        self.ui_func_002bf9f0_ret = 0

    def handle_call(self, uc, address, size, user_data):
        stub_name = user_data
        r0 = uc.reg_read(UC_ARM_REG_R0)
        r1 = uc.reg_read(UC_ARM_REG_R1)
        r2 = uc.reg_read(UC_ARM_REG_R2)
        r3 = uc.reg_read(UC_ARM_REG_R3)
        self.calls.append({
            'name': stub_name,
            'r0': r0, 'r1': r1, 'r2': r2, 'r3': r3,
        })

        if stub_name == 'ui_func_002c0ac8':
            uc.reg_write(UC_ARM_REG_R0, self.work_ptr)
        elif stub_name == 'func_002c00e8':
            uc.reg_write(UC_ARM_REG_R0, self.func_002c00e8_ret)
        elif stub_name in ('UiEngine_GetContext', 'engine_func_002c2b1c'):
            uc.reg_write(UC_ARM_REG_R0, self.ctx_ptr)
        elif stub_name == 'battle_func_002b6e60':
            uc.reg_write(UC_ARM_REG_R0, self.btl_ptr)
        elif stub_name == 'ui_func_002bf9f0':
            uc.reg_write(UC_ARM_REG_R0, self.ui_func_002bf9f0_ret)
        elif stub_name == 'func_002bfcb4':
            uc.reg_write(UC_ARM_REG_R0, 7) # dummy return
        else:
            uc.reg_write(UC_ARM_REG_R0, 0)

        lr = uc.reg_read(UC_ARM_REG_LR)
        uc.reg_write(UC_ARM_REG_PC, lr)

def setup_orig_stubs(uc, tracker):
    for addr, name in ORIG_ADDR_MAP.items():
        uc.mem_write(addr, b"\x1e\xff\x2f\xe1") # bx lr
        uc.hook_add(unicorn.UC_HOOK_CODE, tracker.handle_call, user_data=name, begin=addr, end=addr)

def setup_stubs(uc, tracker):
    for name, addr in STUB_MAP.items():
        uc.mem_write(addr, b"\x1e\xff\x2f\xe1") # bx lr
        uc.hook_add(unicorn.UC_HOOK_CODE, tracker.handle_call, user_data=name, begin=addr, end=addr)
    setup_orig_stubs(uc, tracker)

def compile_source(source_path: Path, func_name: str, build_subdir: str):
    build_dir = ROOT / "build" / build_subdir
    build_dir.mkdir(parents=True, exist_ok=True)
    obj = build_dir / f"{source_path.stem}.o"
    res = compile_tu_armv6k(source_path, obj, repo_root=ROOT)
    if res.returncode != 0:
        print(f"COMPILATION FAILED for {source_path}:")
        print(res.stderr)
        sys.exit(1)
    functions = extract_elf_functions_detailed(obj)
    data = obj.read_bytes()
    e_shoff = struct.unpack_from('<I', data, 32)[0]
    e_shentsize = struct.unpack_from('<H', data, 46)[0]
    e_shnum = struct.unpack_from('<H', data, 48)[0]
    sections = [struct.unpack_from('<IIIIIIIIII', data, e_shoff + i * e_shentsize) for i in range(e_shnum)]
    shstr = sections[struct.unpack_from('<H', data, 50)[0]]
    shstrtab = data[shstr[4]:shstr[4]+shstr[5]]
    def get_sh_name(off):
        return shstrtab[off:].split(b'\x00')[0].decode('ascii')
    rodata = b""
    for s in sections:
        if get_sh_name(s[0]).startswith(".rodata"):
            rodata = data[s[4]:s[4]+s[5]]
            break
    for mangled, (b, relocs) in functions.items():
        if func_name in mangled:
            return b, relocs, rodata
    raise KeyError(f"Function {func_name} not found in {obj}")

def apply_relocations(code_bytes, relocs, target_addr, rodata_addr, extra_syms=None):
    mutable = bytearray(code_bytes)
    syms = dict(STUB_MAP)
    if extra_syms:
        syms.update(extra_syms)

    for rel in relocs:
        offset = rel.offset
        name = rel.symbol_name
        rel_type = rel.relocation_type
        if not name or name.startswith(".rodata"):
            sym_val = rodata_addr
        elif name in syms:
            sym_val = syms[name]
        elif name.endswith(".cpp"):
            sym_val = target_addr
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

def test_infowin_showmessage():
    print("\n--- Testing InfoWin_ShowMessage (0x0010b1b4, 172 B) ---")
    orig_code = ORIG_DATA[0x0010b1b4 - CODE_BASE : 0x0010b1b4 - CODE_BASE + 172]
    decomp_code, relocs, rodata = compile_source(SOURCE, "InfoWin_ShowMessage", "win_batch4_test")

    TARGET_DECOMP = 0x00380000
    RODATA_ADDR = 0x004A0000
    patched_code = apply_relocations(decomp_code, relocs, TARGET_DECOMP, RODATA_ADDR)

    def run_case(code, addr, is_orig, b60, b63, b99):
        uc = create_emulator()
        uc.mem_write(CODE_BASE, ORIG_DATA)
        tracker = StubTracker(uc)
        if is_orig:
            setup_orig_stubs(uc, tracker)
        else:
            uc.mem_write(addr, code)
            setup_stubs(uc, tracker)

        WORK_ADDR = tracker.work_ptr
        CHILD_OBJ = 0x00458000
        SOUND_PTR = 0x0044EA00
        SOUND_OBJ = 0x00490000

        uc.mem_write(SOUND_PTR, struct.pack('<I', SOUND_OBJ))

        # Setup work buffer
        work_buf = bytearray(0x1000)
        struct.pack_into('<I', work_buf, 4, CHILD_OBJ)
        work_buf[0xF60] = b60
        work_buf[0xF63] = b63
        work_buf[0xF99] = b99
        uc.mem_write(WORK_ADDR, bytes(work_buf))

        # Setup child obj buffer
        child_buf = bytearray(0x40)
        uc.mem_write(CHILD_OBJ, bytes(child_buf))

        uc.reg_write(UC_ARM_REG_R0, 0)
        uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
        uc.reg_write(UC_ARM_REG_LR, 0x00000000)

        uc.emu_start(addr, 0x00000000, timeout=100000)

        res_work = uc.mem_read(WORK_ADDR, 0x1000)
        res_child = uc.mem_read(CHILD_OBJ, 0x40)

        return {
            'f62': res_work[0xF62],
            'f63': res_work[0xF63],
            'child_w14': struct.unpack_from('<i', res_child, 0x14)[0],
            'child_w18': struct.unpack_from('<i', res_child, 0x18)[0],
        }, tracker.calls

    for b60, b63, b99 in [(1, 0, 1), (1, 0, 0), (0, 0, 1), (1, 1, 1)]:
        f_orig, c_orig = run_case(orig_code, 0x0010b1b4, True, b60, b63, b99)
        f_dec, c_dec = run_case(patched_code, TARGET_DECOMP, False, b60, b63, b99)

        assert f_orig == f_dec, f"State mismatch ({b60},{b63},{b99}): orig={f_orig}, dec={f_dec}"
        assert len(c_orig) == len(c_dec), f"Call count mismatch ({b60},{b63},{b99}): orig={len(c_orig)}, dec={len(c_dec)}"
        for i in range(len(c_orig)):
            if c_orig[i]['name'] != c_dec[i]['name'] or c_orig[i]['r0'] != c_dec[i]['r0']:
                print(f"Diff call {i}: orig={c_orig[i]} dec={c_dec[i]}")
            assert c_orig[i]['name'] == c_dec[i]['name'], f"Call {i} name mismatch"
            assert c_orig[i]['r0'] == c_dec[i]['r0'], f"Call {i} r0 mismatch"
    print("  [PASS] InfoWin_ShowMessage passes across all 4 conditional branches!")

def test_infowin_updatetimer():
    print("\n--- Testing InfoWin_UpdateTimer (0x0010b260, 192 B) ---")
    orig_code = ORIG_DATA[0x0010b260 - CODE_BASE : 0x0010b260 - CODE_BASE + 192]
    decomp_code, relocs, rodata = compile_source(SOURCE, "InfoWin_UpdateTimer", "win_batch4_test")

    TARGET_DECOMP = 0x00380000
    RODATA_ADDR = 0x004A0000
    patched_code = apply_relocations(decomp_code, relocs, TARGET_DECOMP, RODATA_ADDR)

    def run_case(code, addr, is_orig, ret_2c00e8, b60, b64, b65, b99):
        uc = create_emulator()
        uc.mem_write(CODE_BASE, ORIG_DATA)
        tracker = StubTracker(uc)
        tracker.func_002c00e8_ret = ret_2c00e8
        if is_orig:
            setup_orig_stubs(uc, tracker)
        else:
            uc.mem_write(addr, code)
            setup_stubs(uc, tracker)

        WORK_ADDR = tracker.work_ptr
        CHILD_OBJ = 0x00459000
        SOUND_PTR = 0x0044EA00
        SOUND_OBJ = 0x00490000

        uc.mem_write(SOUND_PTR, struct.pack('<I', SOUND_OBJ))

        work_buf = bytearray(0x1000)
        struct.pack_into('<I', work_buf, 8, CHILD_OBJ)
        work_buf[0xF60] = b60
        work_buf[0xF64] = b64
        work_buf[0xF65] = b65
        work_buf[0xF99] = b99
        uc.mem_write(WORK_ADDR, bytes(work_buf))

        child_buf = bytearray(0x40)
        uc.mem_write(CHILD_OBJ, bytes(child_buf))

        uc.reg_write(UC_ARM_REG_R0, 0)
        uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
        uc.reg_write(UC_ARM_REG_LR, 0x00000000)

        uc.emu_start(addr, 0x00000000, timeout=100000)

        res_work = uc.mem_read(WORK_ADDR, 0x1000)
        res_child = uc.mem_read(CHILD_OBJ, 0x40)

        return {
            'f62': res_work[0xF62],
            'f64': res_work[0xF64],
            'f65': res_work[0xF65],
            'child_w14': struct.unpack_from('<i', res_child, 0x14)[0],
            'child_w18': struct.unpack_from('<i', res_child, 0x18)[0],
        }, tracker.calls

    cases = [
        (1, 0, 0, 0, 0), # ret != 0 -> sets f65 = 1
        (0, 0, 0, 0, 0), # b60 == 0 -> early return
        (0, 1, 1, 0, 0), # b64 != 0 -> early return
        (0, 1, 0, 1, 0), # b65 != 0 -> early return
        (0, 1, 0, 0, 1), # full path with sound
        (0, 1, 0, 0, 0), # full path without sound
    ]
    for ret, b60, b64, b65, b99 in cases:
        f_orig, c_orig = run_case(orig_code, 0x0010b260, True, ret, b60, b64, b65, b99)
        f_dec, c_dec = run_case(patched_code, TARGET_DECOMP, False, ret, b60, b64, b65, b99)

        assert f_orig == f_dec, f"State mismatch: orig={f_orig}, dec={f_dec}"
        assert len(c_orig) == len(c_dec), f"Call count mismatch: orig={len(c_orig)}, dec={len(c_dec)}"
        for i in range(len(c_orig)):
            assert c_orig[i]['name'] == c_dec[i]['name']
            assert c_orig[i]['r0'] == c_dec[i]['r0']
    print("  [PASS] InfoWin_UpdateTimer passes across all 6 conditional branches!")

def test_guestwin_handleprompt():
    print("\n--- Testing GuestWin_HandlePrompt (0x0010b510, 104 B) ---")
    orig_code = ORIG_DATA[0x0010b510 - CODE_BASE : 0x0010b510 - CODE_BASE + 104]
    decomp_code, relocs, rodata = compile_source(SOURCE, "GuestWin_HandlePrompt", "win_batch4_test")

    TARGET_DECOMP = 0x00380000
    RODATA_ADDR = 0x004A0000
    patched_code = apply_relocations(decomp_code, relocs, TARGET_DECOMP, RODATA_ADDR)

    def run_case(code, addr, is_orig, pattern):
        uc = create_emulator()
        uc.mem_write(CODE_BASE, ORIG_DATA)
        tracker = StubTracker(uc)
        if is_orig:
            setup_orig_stubs(uc, tracker)
        else:
            uc.mem_write(addr, code)
            setup_stubs(uc, tracker)

        CTX_ADDR = tracker.ctx_ptr
        ctx_buf = bytearray(0x5000)

        # Setup 16 slots with varied flags and timers
        for i in range(16):
            flags = pattern[i][0]
            timer = pattern[i][1]
            ctx_buf[0x3C80 + i * 0x14] = flags
            struct.pack_into('<h', ctx_buf, 0xF28 + i * 0x14, timer)

        uc.mem_write(CTX_ADDR, bytes(ctx_buf))

        uc.reg_write(UC_ARM_REG_R0, 0)
        uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
        uc.reg_write(UC_ARM_REG_LR, 0x00000000)

        uc.emu_start(addr, 0x00000000, timeout=100000)

        res_ctx = uc.mem_read(CTX_ADDR, 0x5000)
        out_slots = []
        for i in range(16):
            fl = res_ctx[0x3C80 + i * 0x14]
            tm = struct.unpack_from('<h', res_ctx, 0xF28 + i * 0x14)[0]
            out_slots.append((fl, tm))
        return out_slots, tracker.calls

    # Test patterns:
    # flags & 7 == 7 and not (flags & 8):
    # slot 0: 7, timer 5 -> timer 4, flags 7
    # slot 1: 7, timer 1 -> timer 0, flags 7 | 8 = 15
    # slot 2: 7, timer 0 -> timer 0, flags 7 | 8 = 15
    # slot 3: 15, timer 5 -> flags & 8 set -> skipped
    # slot 4: 3, timer 5 -> flags & 7 != 7 -> skipped
    # slot 5: 5, timer 5 -> flags & 7 != 7 -> skipped
    pattern1 = [(7, 5), (7, 1), (7, 0), (15, 5), (3, 5), (5, 5)] + [(7, 10)] * 10
    pattern2 = [(0, 0)] * 16

    for pat in [pattern1, pattern2]:
        f_orig, c_orig = run_case(orig_code, 0x0010b510, True, pat)
        f_dec, c_dec = run_case(patched_code, TARGET_DECOMP, False, pat)

        assert f_orig == f_dec, f"Slots mismatch: orig={f_orig}, dec={f_dec}"
        assert len(c_orig) == len(c_dec)
        for i in range(len(c_orig)):
            assert c_orig[i]['name'] == c_dec[i]['name']
    print("  [PASS] GuestWin_HandlePrompt passes across 16-slot matrix!")

def test_guestwin_calc():
    print("\n--- Testing GuestWin_Calc (0x0011b128, 148 B) ---")
    orig_code = ORIG_DATA[0x0011b128 - CODE_BASE : 0x0011b128 - CODE_BASE + 148]
    decomp_code, relocs, rodata = compile_source(SOURCE, "GuestWin_Calc", "win_batch4_test")

    TARGET_DECOMP = 0x00380000
    RODATA_ADDR = 0x004A0000
    patched_code = apply_relocations(decomp_code, relocs, TARGET_DECOMP, RODATA_ADDR)

    def run_case(code, addr, is_orig, active_flag, state, timer, ret_2bf9f0):
        uc = create_emulator()
        uc.mem_write(CODE_BASE, ORIG_DATA)
        tracker = StubTracker(uc)
        tracker.ui_func_002bf9f0_ret = ret_2bf9f0
        if is_orig:
            setup_orig_stubs(uc, tracker)
        else:
            uc.mem_write(addr, code)
            setup_stubs(uc, tracker)

        BTL_ADDR = tracker.btl_ptr
        btl_buf = bytearray(0x100)
        struct.pack_into('<H', btl_buf, 0x46, active_flag)
        uc.mem_write(BTL_ADDR, bytes(btl_buf))

        GUEST_ADDR = 0x00454000
        PTR_ADDR = 0x0043E110
        uc.mem_write(PTR_ADDR, struct.pack('<I', GUEST_ADDR))

        guest_buf = bytearray(0x100)
        struct.pack_into('<I', guest_buf, 8, state)
        struct.pack_into('<I', guest_buf, 0xC, timer)
        uc.mem_write(GUEST_ADDR, bytes(guest_buf))

        uc.reg_write(UC_ARM_REG_R0, 0)
        uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
        uc.reg_write(UC_ARM_REG_LR, 0x00000000)

        uc.emu_start(addr, 0x00000000, timeout=100000)

        res_guest = uc.mem_read(GUEST_ADDR, 0x100)
        return {
            'state': struct.unpack_from('<I', res_guest, 8)[0],
            'timer': struct.unpack_from('<I', res_guest, 0xC)[0],
        }, tracker.calls

    # Test cases:
    # (active, state, timer, ret_2bf9f0)
    cases = [
        (0, 1, 10, 1), # active == 0 -> early return, no tick
        (1, 0, 10, 1), # state == 0 -> timer++ (11)
        (1, 1, 10, 0), # state == 1, ret == 0 -> timer++ (11)
        (1, 1, 10, 1), # state == 1, ret != 0 -> state=2, timer=0, then timer++ (1)
        (1, 2, 10, 1), # state == 2 -> timer++ (11)
        (1, 3, 10, 0), # state == 3, ret == 0 -> timer++ (11)
        (1, 3, 10, 1), # state == 3, ret != 0 -> state=0, timer++ (11)
    ]

    for active, state, timer, ret in cases:
        f_orig, c_orig = run_case(orig_code, 0x0011b128, True, active, state, timer, ret)
        f_dec, c_dec = run_case(patched_code, TARGET_DECOMP, False, active, state, timer, ret)

        assert f_orig == f_dec, f"State mismatch: orig={f_orig}, dec={f_dec}"
        assert len(c_orig) == len(c_dec)
        for i in range(len(c_orig)):
            assert c_orig[i]['name'] == c_dec[i]['name']
            assert c_orig[i]['r0'] == c_dec[i]['r0']
    print("  [PASS] GuestWin_Calc passes across all 7 state machine transitions!")

def main():
    print("Testing Window Batch 4 functions...")
    test_infowin_showmessage()
    test_infowin_updatetimer()
    test_guestwin_handleprompt()
    test_guestwin_calc()
    print("\nALL 4 WINDOW BATCH 4 FUNCTIONS PASSED 100%!")

if __name__ == "__main__":
    main()
