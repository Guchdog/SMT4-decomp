#!/usr/bin/env python3
"""Differential test runner for window batch 2 candidates against code.bin.

Tests:
  - 0x002cecd8: SearchWin_IsActive (52 B)
  - 0x0026385c: PlaceWin_SetPos (64 B)
  - 0x0026389c: PlaceWin_SetScale (64 B)
  - 0x00263910: PlaceWin_CheckState (60 B)
  - 0x0026394c: PlaceWin_IsActive (44 B)
  - 0x00263978: PlaceWin_ShowMessage (124 B)
"""

import struct
import sys
from pathlib import Path
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_ARM, UC_PROT_READ, UC_PROT_WRITE, UC_PROT_EXEC
from unicorn.arm_const import *
import unicorn

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools.build_check import compile_tu_armv6k
from tools.asm_diff import extract_elf_functions_detailed

CODE_BIN = ROOT / "extracted" / "exefs" / "code.bin"
SOURCE = ROOT / "src" / "ui" / "window.cpp"

CODE_BASE = 0x00100000
CODE_SIZE = 0x00400000
STACK_BASE = 0x0FFF0000
STACK_SIZE = 0x00010000
STACK_TOP = STACK_BASE + STACK_SIZE - 0x1000

BUILD_DIR = ROOT / "build" / "window_batch2_test"

ORIG_DATA = CODE_BIN.read_bytes()

COMPILED_FUNCTIONS = None
RODATA_ADDR = 0x004A0000
RODATA_BYTES = b""

# Globals
ADDR_SEARCHWIN_CTX   = 0x0043E2A8
ADDR_PLACEWIN_WORK   = 0x0043E140
ADDR_POS_SLOTS       = 0x004D9880
ADDR_SCALE_SLOTS     = 0x004D9D88

# Stubs
STUB_BASE = 0x004B0000
STUB_MAP = {
    'engine_func_002c2be8': STUB_BASE + 0x00,
    'script_vm_func_0025a274': STUB_BASE + 0x08,
    'ui_func_002d569c': STUB_BASE + 0x10,
    'ui_func_002d56fc': STUB_BASE + 0x18,
    'UiAnimSprite_SetAnim': STUB_BASE + 0x20,
    'AsdMem_Zero': STUB_BASE + 0x28,
    'AsdString_Strcpy': STUB_BASE + 0x30,
}

ORIG_ADDR_MAP = {
    0x002c2be8: 'engine_func_002c2be8',
    0x0025a274: 'script_vm_func_0025a274',
    0x002d569c: 'ui_func_002d569c',
    0x002d56fc: 'ui_func_002d56fc',
    0x002bf030: 'UiAnimSprite_SetAnim',
    0x002c4b30: 'AsdMem_Zero',
    0x002c5ff4: 'AsdString_Strcpy',
}

def compile_function(func_name: str, out: Path = BUILD_DIR, source: Path = SOURCE):
    global COMPILED_FUNCTIONS, RODATA_BYTES
    if COMPILED_FUNCTIONS is None:
        out.mkdir(parents=True, exist_ok=True)
        obj = out / "window.o"
        res = compile_tu_armv6k(source, obj, repo_root=ROOT)
        if res.returncode != 0:
            print("COMPILATION FAILED:")
            print(res.stderr)
            sys.exit(1)
        COMPILED_FUNCTIONS = extract_elf_functions_detailed(obj)
        data = obj.read_bytes()
        e_shoff = struct.unpack_from('<I', data, 32)[0]
        e_shentsize = struct.unpack_from('<H', data, 46)[0]
        e_shnum = struct.unpack_from('<H', data, 48)[0]
        sections = [struct.unpack_from('<IIIIIIIIII', data, e_shoff + i * e_shentsize) for i in range(e_shnum)]
        shstr = sections[struct.unpack_from('<H', data, 50)[0]]
        shstrtab = data[shstr[4]:shstr[4]+shstr[5]]
        def get_sh_name(off):
            return shstrtab[off:].split(b'\x00')[0].decode('ascii')
        for s in sections:
            sh_name = get_sh_name(s[0])
            if sh_name.startswith(".rodata"):
                RODATA_BYTES = data[s[4]:s[4]+s[5]]
                break

    for mangled, (b, relocs) in COMPILED_FUNCTIONS.items():
        if func_name in mangled:
            return b, relocs
    raise KeyError(f"Function {func_name} not found in compiled object")

class Emulator:
    def __init__(self):
        self.uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
        self.uc.mem_map(CODE_BASE, CODE_SIZE, UC_PROT_READ | UC_PROT_WRITE | UC_PROT_EXEC)
        self.uc.mem_write(CODE_BASE, ORIG_DATA[:CODE_SIZE])
        self.uc.mem_map(STACK_BASE, STACK_SIZE, UC_PROT_READ | UC_PROT_WRITE)

        try:
            self.uc.reg_write(UC_ARM_REG_C1_C0_2, 0x00F00000)
            self.uc.reg_write(UC_ARM_REG_FPEXC, 0x40000000)
        except Exception:
            pass

        self.call_log = []
        self.script_ret = 1
        self.ui_ret1 = 1
        self.ui_ret2 = 1

        self._install_stubs()

    def _install_stubs(self):
        bx_lr = struct.pack('<I', 0xe12fff1e)

        for name, addr in STUB_MAP.items():
            self.uc.mem_write(addr, bx_lr)
            self.uc.hook_add(unicorn.UC_HOOK_CODE, self._make_hook(name), begin=addr, end=addr)

        for addr, name in ORIG_ADDR_MAP.items():
            self.uc.mem_write(addr, bx_lr)
            self.uc.hook_add(unicorn.UC_HOOK_CODE, self._make_hook(name), begin=addr, end=addr)

    def _make_hook(self, name):
        def hook(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            r1 = uc.reg_read(UC_ARM_REG_R1)
            r2 = uc.reg_read(UC_ARM_REG_R2)

            if name == 'engine_func_002c2be8':
                self.call_log.append((name, r0))
                uc.reg_write(UC_ARM_REG_R0, 0x12345678)
            elif name == 'script_vm_func_0025a274':
                self.call_log.append((name, r0))
                uc.reg_write(UC_ARM_REG_R0, self.script_ret)
            elif name == 'ui_func_002d569c':
                self.call_log.append((name, r0))
                uc.reg_write(UC_ARM_REG_R0, self.ui_ret1)
            elif name == 'ui_func_002d56fc':
                self.call_log.append((name, r0))
                uc.reg_write(UC_ARM_REG_R0, self.ui_ret2)
            elif name == 'UiAnimSprite_SetAnim':
                self.call_log.append((name, r0, r1, r2))
            elif name == 'AsdMem_Zero':
                self.call_log.append((name, r0, r1))
                uc.mem_write(r0, b'\x00' * r1)
            elif name == 'AsdString_Strcpy':
                src_str = uc.mem_read(r1, 128).split(b'\x00')[0]
                uc.mem_write(r0, bytes(src_str + b'\x00'))
                self.call_log.append((name, r0, src_str.decode('ascii', errors='ignore')))
            else:
                self.call_log.append((name, r0, r1, r2))
        return hook

def relocate_compiled(b: bytes, relocs: list, base_addr: int) -> bytearray:
    code = bytearray(b)
    sym_map = dict(STUB_MAP)
    sym_map.update({
        '_ZN4smt42ui14g_PlaceWinWorkE': ADDR_PLACEWIN_WORK,
    })

    for rel in relocs:
        off = rel.offset
        sym = rel.symbol_name
        rel_type = rel.relocation_type

        if sym in sym_map:
            target = sym_map[sym]
        else:
            raise RuntimeError(f"Unmapped relocation: {sym}")

        if rel_type in (28, 29):  # R_ARM_CALL / R_ARM_JUMP24
            curr = struct.unpack_from('<I', code, off)[0]
            disp = (target - (base_addr + off + 8)) >> 2
            new_disp = disp & 0x00FFFFFF
            new_inst = (curr & 0xFF000000) | new_disp
            struct.pack_into('<I', code, off, new_inst)
        elif rel_type == 2:  # R_ARM_ABS32
            curr = struct.unpack_from('<I', code, off)[0]
            struct.pack_into('<I', code, off, target + curr)
        else:
            raise RuntimeError(f"Unsupported relocation type: {rel_type}")
    return code

def run_function(emu: Emulator, addr: int, args: list, stack_top: int = STACK_TOP):
    emu.uc.reg_write(UC_ARM_REG_SP, stack_top)
    emu.uc.reg_write(UC_ARM_REG_LR, 0x00000000)
    reg_list = [UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3]
    for i, val in enumerate(args[:4]):
        emu.uc.reg_write(reg_list[i], val)
    if len(args) > 4:
        for j, val in enumerate(args[4:]):
            emu.uc.mem_write(stack_top + j * 4, struct.pack('<I', val))

    end_addr = 0x00000000
    emu.uc.emu_start(addr, end_addr)
    return emu.uc.reg_read(UC_ARM_REG_R0)

def test_searchwin_isactive():
    print("\n--- Testing SearchWin_IsActive (0x002cecd8, 52 B) ---")
    orig_addr = 0x002cecd8
    comp_addr = 0x003D0000
    b, relocs = compile_function("SearchWin_IsActive")
    relocated = relocate_compiled(b, relocs, comp_addr)

    ctx_addr = 0x00470000

    scenarios = [
        ("count_under_cap", 10, 11),
        ("count_at_cap", 0x270E, 0x270E),
        ("count_above_cap", 0x3000, 0x270E),
    ]

    for name, init_val, expected_val in scenarios:
        # Orig
        emu_orig = Emulator()
        emu_orig.uc.mem_write(ADDR_SEARCHWIN_CTX + 4, struct.pack('<I', ctx_addr))
        emu_orig.uc.mem_write(ctx_addr + 0x66, struct.pack('<H', init_val))
        run_function(emu_orig, orig_addr, [])
        orig_val = struct.unpack('<H', emu_orig.uc.mem_read(ctx_addr + 0x66, 2))[0]

        # Comp
        emu_comp = Emulator()
        emu_comp.uc.mem_write(comp_addr, bytes(relocated))
        emu_comp.uc.mem_write(ADDR_SEARCHWIN_CTX + 4, struct.pack('<I', ctx_addr))
        emu_comp.uc.mem_write(ctx_addr + 0x66, struct.pack('<H', init_val))
        run_function(emu_comp, comp_addr, [])
        comp_val = struct.unpack('<H', emu_comp.uc.mem_read(ctx_addr + 0x66, 2))[0]

        assert orig_val == comp_val == expected_val, f"{name}: val mismatch: orig={orig_val}, comp={comp_val}"
        print(f"  [PASS] {name} (val={comp_val})")

def test_placewin_setpos():
    print("\n--- Testing PlaceWin_SetPos (0x0026385c, 64 B) ---")
    orig_addr = 0x0026385c
    comp_addr = 0x003D0000
    b, relocs = compile_function("PlaceWin_SetPos")
    relocated = relocate_compiled(b, relocs, comp_addr)

    slot_ptr = 0x00472000
    obj_ptr = 0x00473000

    # Layer 1, index 2:
    layer = 1
    idx = 2
    stride = layer * 161
    slot_entry = ADDR_POS_SLOTS + 0x264 + (stride + idx) * 4

    # Floats: x=1.5, y=2.5, z=3.5 (passed in VFP s0, s1, s2)
    # Orig
    emu_orig = Emulator()
    emu_orig.uc.mem_write(slot_entry, struct.pack('<I', slot_ptr))
    emu_orig.uc.mem_write(slot_ptr + 8, struct.pack('<I', obj_ptr))
    emu_orig.uc.reg_write(UC_ARM_REG_S0, struct.unpack('<I', struct.pack('<f', 1.5))[0])
    emu_orig.uc.reg_write(UC_ARM_REG_S1, struct.unpack('<I', struct.pack('<f', 2.5))[0])
    emu_orig.uc.reg_write(UC_ARM_REG_S2, struct.unpack('<I', struct.pack('<f', 3.5))[0])
    run_function(emu_orig, orig_addr, [idx, layer])
    orig_floats = struct.unpack('<4f', emu_orig.uc.mem_read(obj_ptr + 0xB8, 16))
    orig_c8 = struct.unpack('<I', emu_orig.uc.mem_read(obj_ptr + 0xC8, 4))[0]

    # Comp
    emu_comp = Emulator()
    emu_comp.uc.mem_write(comp_addr, bytes(relocated))
    emu_comp.uc.mem_write(slot_entry, struct.pack('<I', slot_ptr))
    emu_comp.uc.mem_write(slot_ptr + 8, struct.pack('<I', obj_ptr))
    emu_comp.uc.reg_write(UC_ARM_REG_S0, struct.unpack('<I', struct.pack('<f', 1.5))[0])
    emu_comp.uc.reg_write(UC_ARM_REG_S1, struct.unpack('<I', struct.pack('<f', 2.5))[0])
    emu_comp.uc.reg_write(UC_ARM_REG_S2, struct.unpack('<I', struct.pack('<f', 3.5))[0])
    run_function(emu_comp, comp_addr, [idx, layer])
    comp_floats = struct.unpack('<4f', emu_comp.uc.mem_read(obj_ptr + 0xB8, 16))
    comp_c8 = struct.unpack('<I', emu_comp.uc.mem_read(obj_ptr + 0xC8, 4))[0]

    assert orig_floats == comp_floats == (1.5, 2.5, 3.5, 1.0), f"floats mismatch: orig={orig_floats}, comp={comp_floats}"
    assert orig_c8 == comp_c8 == 0x12345678, f"c8 mismatch: orig={orig_c8}, comp={comp_c8}"
    print(f"  [PASS] PlaceWin_SetPos (floats={comp_floats}, field_C8={hex(comp_c8)})")

def test_placewin_setscale():
    print("\n--- Testing PlaceWin_SetScale (0x0026389c, 64 B) ---")
    orig_addr = 0x0026389c
    comp_addr = 0x003D0000
    b, relocs = compile_function("PlaceWin_SetScale")
    relocated = relocate_compiled(b, relocs, comp_addr)

    slot_ptr = 0x00472000
    obj_ptr = 0x00473000
    layer = 0
    idx = 1
    stride = layer * 161
    slot_entry = ADDR_SCALE_SLOTS + 0x264 + (stride + idx) * 4

    scenarios = [
        ("negative_index_rejected", -1, 0, (0.0, 0.0, 0.0, 0.0), 0),
        ("valid_index_applied", 1, 0, (2.0, 3.0, 4.0, 5.0), 0x12345678),
    ]

    for name, t_idx, t_layer, scales, expected_c8 in scenarios:
        # Orig
        emu_orig = Emulator()
        emu_orig.uc.mem_write(slot_entry, struct.pack('<I', slot_ptr))
        emu_orig.uc.mem_write(slot_ptr + 8, struct.pack('<I', obj_ptr))
        emu_orig.uc.mem_write(obj_ptr + 0x100, b'\x00' * 4)
        emu_orig.uc.reg_write(UC_ARM_REG_S0, struct.unpack('<I', struct.pack('<f', scales[0]))[0])
        emu_orig.uc.reg_write(UC_ARM_REG_S1, struct.unpack('<I', struct.pack('<f', scales[1]))[0])
        emu_orig.uc.reg_write(UC_ARM_REG_S2, struct.unpack('<I', struct.pack('<f', scales[2]))[0])
        emu_orig.uc.reg_write(UC_ARM_REG_S3, struct.unpack('<I', struct.pack('<f', scales[3]))[0])
        run_function(emu_orig, orig_addr, [t_idx, t_layer])
        orig_scales = struct.unpack('<4f', emu_orig.uc.mem_read(obj_ptr + 0xCC, 16))
        orig_c8 = struct.unpack('<I', emu_orig.uc.mem_read(obj_ptr + 0x100, 4))[0]

        # Comp
        emu_comp = Emulator()
        emu_comp.uc.mem_write(comp_addr, bytes(relocated))
        emu_comp.uc.mem_write(slot_entry, struct.pack('<I', slot_ptr))
        emu_comp.uc.mem_write(slot_ptr + 8, struct.pack('<I', obj_ptr))
        emu_comp.uc.mem_write(obj_ptr + 0x100, b'\x00' * 4)
        emu_comp.uc.reg_write(UC_ARM_REG_S0, struct.unpack('<I', struct.pack('<f', scales[0]))[0])
        emu_comp.uc.reg_write(UC_ARM_REG_S1, struct.unpack('<I', struct.pack('<f', scales[1]))[0])
        emu_comp.uc.reg_write(UC_ARM_REG_S2, struct.unpack('<I', struct.pack('<f', scales[2]))[0])
        emu_comp.uc.reg_write(UC_ARM_REG_S3, struct.unpack('<I', struct.pack('<f', scales[3]))[0])
        run_function(emu_comp, comp_addr, [t_idx, t_layer])
        comp_scales = struct.unpack('<4f', emu_comp.uc.mem_read(obj_ptr + 0xCC, 16))
        comp_c8 = struct.unpack('<I', emu_comp.uc.mem_read(obj_ptr + 0x100, 4))[0]

        assert orig_scales == comp_scales, f"{name}: scales mismatch"
        assert orig_c8 == comp_c8 == expected_c8, f"{name}: c8 mismatch: orig={orig_c8}, comp={comp_c8}"
        print(f"  [PASS] {name} (scales={comp_scales}, field_100={hex(comp_c8)})")

def test_placewin_checkstate():
    print("\n--- Testing PlaceWin_CheckState (0x00263910, 60 B) ---")
    orig_addr = 0x00263910
    comp_addr = 0x003D0000
    b, relocs = compile_function("PlaceWin_CheckState")
    relocated = relocate_compiled(b, relocs, comp_addr)

    ctx = 0x00474000
    scenarios = [
        ("all_true_returns_1", 1, 1, 1, 1),
        ("script_false_returns_0", 0, 1, 1, 0),
        ("ui1_false_returns_0", 1, 0, 1, 0),
        ("ui2_false_returns_0", 1, 1, 0, 0),
    ]

    for name, s_ret, u1_ret, u2_ret, expected in scenarios:
        # Orig
        emu_orig = Emulator()
        emu_orig.script_ret = s_ret
        emu_orig.ui_ret1 = u1_ret
        emu_orig.ui_ret2 = u2_ret
        emu_orig.uc.mem_write(ctx + 8, struct.pack('<I', 0x55))
        ret_orig = run_function(emu_orig, orig_addr, [ctx])

        # Comp
        emu_comp = Emulator()
        emu_comp.uc.mem_write(comp_addr, bytes(relocated))
        emu_comp.script_ret = s_ret
        emu_comp.ui_ret1 = u1_ret
        emu_comp.ui_ret2 = u2_ret
        emu_comp.uc.mem_write(ctx + 8, struct.pack('<I', 0x55))
        ret_comp = run_function(emu_comp, comp_addr, [ctx])

        assert ret_orig == ret_comp == expected, f"{name}: ret mismatch: orig={ret_orig}, comp={ret_comp}"
        print(f"  [PASS] {name} (ret={ret_comp})")

def test_placewin_isactive():
    print("\n--- Testing PlaceWin_IsActive (0x0026394c, 44 B) ---")
    orig_addr = 0x0026394c
    comp_addr = 0x003D0000
    b, relocs = compile_function("PlaceWin_IsActive")
    relocated = relocate_compiled(b, relocs, comp_addr)

    ctx = 0x00474000
    obj = 0x00475000

    scenarios = [
        ("null_object_returns_1", 0, 0.0, 0.0, 1),
        ("v2_less_than_v1_returns_1", obj, 10.0, 5.0, 1),
        ("v2_equal_to_v1_returns_1", obj, 10.0, 10.0, 1),
        ("v2_greater_than_v1_returns_0", obj, 10.0, 15.0, 0),
    ]

    for name, obj_target, v1, v2, expected in scenarios:
        # Orig
        emu_orig = Emulator()
        emu_orig.uc.mem_write(ctx + 4, struct.pack('<I', obj_target))
        if obj_target != 0:
            emu_orig.uc.mem_write(obj_target + 0x38, struct.pack('<f', v1))
            emu_orig.uc.mem_write(obj_target + 0x48, struct.pack('<f', v2))
        ret_orig = run_function(emu_orig, orig_addr, [ctx])

        # Comp
        emu_comp = Emulator()
        emu_comp.uc.mem_write(comp_addr, bytes(relocated))
        emu_comp.uc.mem_write(ctx + 4, struct.pack('<I', obj_target))
        if obj_target != 0:
            emu_comp.uc.mem_write(obj_target + 0x38, struct.pack('<f', v1))
            emu_comp.uc.mem_write(obj_target + 0x48, struct.pack('<f', v2))
        ret_comp = run_function(emu_comp, comp_addr, [ctx])

        assert ret_orig == ret_comp == expected, f"{name}: ret mismatch: orig={ret_orig}, comp={ret_comp}"
        print(f"  [PASS] {name} (ret={ret_comp})")

def test_placewin_showmessage():
    print("\n--- Testing PlaceWin_ShowMessage (0x00263978, 124 B) ---")
    orig_addr = 0x00263978
    comp_addr = 0x003D0000
    b, relocs = compile_function("PlaceWin_ShowMessage")
    relocated = relocate_compiled(b, relocs, comp_addr)

    work_ptr = 0x00476000
    msg_ptr = 0x00477000

    scenarios = [
        ("short_message", b"Hello\x00"),
        ("longer_message", b"Terminal Message Long String 1234567890\x00"),
    ]

    for name, msg_bytes in scenarios:
        # Orig
        emu_orig = Emulator()
        emu_orig.uc.mem_write(ADDR_PLACEWIN_WORK, struct.pack('<I', work_ptr))
        emu_orig.uc.mem_write(work_ptr, b'\x00' * 0x200)
        emu_orig.uc.mem_write(msg_ptr, msg_bytes)
        run_function(emu_orig, orig_addr, [msg_ptr])
        orig_calls = list(emu_orig.call_log)
        orig_state = struct.unpack('<I', emu_orig.uc.mem_read(work_ptr + 8, 4))[0]
        orig_flags = emu_orig.uc.mem_read(work_ptr + 0x10, 1)[0]
        orig_copied = emu_orig.uc.mem_read(work_ptr + 0xC0, len(msg_bytes)).split(b'\x00')[0]

        # Comp
        emu_comp = Emulator()
        emu_comp.uc.mem_write(comp_addr, bytes(relocated))
        emu_comp.uc.mem_write(ADDR_PLACEWIN_WORK, struct.pack('<I', work_ptr))
        emu_comp.uc.mem_write(work_ptr, b'\x00' * 0x200)
        emu_comp.uc.mem_write(msg_ptr, msg_bytes)
        run_function(emu_comp, comp_addr, [msg_ptr])
        comp_calls = list(emu_comp.call_log)
        comp_state = struct.unpack('<I', emu_comp.uc.mem_read(work_ptr + 8, 4))[0]
        comp_flags = emu_comp.uc.mem_read(work_ptr + 0x10, 1)[0]
        comp_copied = emu_comp.uc.mem_read(work_ptr + 0xC0, len(msg_bytes)).split(b'\x00')[0]

        assert orig_calls == comp_calls, f"{name}: calls mismatch: orig={orig_calls}, comp={comp_calls}"
        assert orig_state == comp_state == 1, f"{name}: state mismatch: orig={orig_state}, comp={comp_state}"
        assert orig_flags == comp_flags == 1, f"{name}: flags mismatch: orig={orig_flags}, comp={comp_flags}"
        assert orig_copied == comp_copied == msg_bytes.split(b'\x00')[0], f"{name}: copied mismatch: {orig_copied} vs {comp_copied}"
        print(f"  [PASS] {name} (state={comp_state}, flags={comp_flags}, text={comp_copied.decode('ascii')})")

def main():
    print("Testing Window Batch 2 candidates...")
    test_searchwin_isactive()
    test_placewin_setpos()
    test_placewin_setscale()
    test_placewin_checkstate()
    test_placewin_isactive()
    test_placewin_showmessage()
    print("\nALL 6 WINDOW BATCH 2 CANDIDATES PASSED 100%!")

if __name__ == "__main__":
    main()
