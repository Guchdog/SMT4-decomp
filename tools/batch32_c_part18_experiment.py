#!/usr/bin/env python3
"""Differential test runner for leaf_batch32_c Part 18 candidates against code.bin.

Tests:
  - 0x002b6030: ui_func_002b6030 (572 B)
  - 0x002b8104: ui_func_002b8104 (1056 B)
  - 0x002bb5c4: func_002bb5c4 (68 B)
  - 0x002c42fc: engine_func_002c42fc (100 B)
  - 0x002f364c: script_vm_func_002f364c (624 B)
"""

import struct
import sys
from pathlib import Path
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_ARM, UC_PROT_READ, UC_PROT_WRITE, UC_PROT_EXEC, UC_HOOK_INTR
from unicorn.arm_const import *
import unicorn

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools.build_check import compile_tu_armv6k
from tools.asm_diff import extract_elf_functions_detailed

CODE_BIN = ROOT / "extracted" / "exefs" / "code.bin"
SOURCE = ROOT / "src" / "engine" / "leaf_batch32_c.cpp"

CODE_BASE = 0x00100000
CODE_SIZE = 0x00400000
STACK_BASE = 0x0FFF0000
STACK_SIZE = 0x00010000
STACK_TOP = STACK_BASE + STACK_SIZE - 0x1000

BUILD_DIR = ROOT / "build" / "batch32_c_part18"

ORIG_DATA = CODE_BIN.read_bytes()

COMPILED_FUNCTIONS = None
COMPILED_ST_VALUES = {}
RODATA_ADDR = 0x10050000
RODATA_BYTES = b""

def load_original_bytes(addr: int, size: int) -> bytes:
    off = addr - CODE_BASE
    return ORIG_DATA[off : off + size]

def compile_function(func_name: str, out: Path = BUILD_DIR, source: Path = SOURCE):
    global COMPILED_FUNCTIONS, COMPILED_ST_VALUES, RODATA_BYTES
    if COMPILED_FUNCTIONS is None:
        out.mkdir(parents=True, exist_ok=True)
        obj = out / "leaf_batch32_c.o"
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
            if get_sh_name(s[0]) == ".rodata":
                RODATA_BYTES = data[s[4]:s[4]+s[5]]
                break

        symtab_sec = [s for s in sections if s[1] == 2][0]
        strtab_sec = sections[symtab_sec[6]]
        strtab_data = data[strtab_sec[4]:strtab_sec[4]+strtab_sec[5]]
        count = symtab_sec[5] // 16
        for i in range(count):
            st_name, st_value, st_size, st_info, st_other, st_shndx = struct.unpack_from('<IIIBBH', data, symtab_sec[4] + i * 16)
            name = strtab_data[st_name:].split(b'\x00')[0].decode('ascii', errors='ignore')
            if name:
                COMPILED_ST_VALUES[name] = st_value
    return COMPILED_FUNCTIONS[func_name]

def stage_body(body: bytes, relocs, target_addr: int, symbol_map: dict[str, int], func_name: str = "") -> bytes:
    data = bytearray(body)
    st_val = COMPILED_ST_VALUES.get(func_name, 0)
    for reloc in relocs:
        sym = reloc.symbol_name
        if sym == "":
            inst = struct.unpack_from("<I", data, reloc.offset)[0]
            if 0 <= inst < len(RODATA_BYTES):
                actual_addr = RODATA_ADDR + inst
            else:
                off_in_fn = inst - st_val
                actual_addr = target_addr + off_in_fn
            struct.pack_into("<I", data, reloc.offset, actual_addr)
            continue
        if sym not in symbol_map:
            raise RuntimeError(f"Unmapped relocation: {sym}")
        stub_addr = symbol_map[sym]
        inst = struct.unpack_from("<I", data, reloc.offset)[0]
        if inst == 0:
            struct.pack_into("<I", data, reloc.offset, stub_addr)
            continue
        rel_off = stub_addr - (target_addr + reloc.offset + 8)
        if (inst & 0xFE000000) == 0xFA000000:
            h = (rel_off >> 1) & 1
            imm24 = (rel_off >> 2) & 0x00FFFFFF
            inst = 0xFA000000 | (h << 24) | imm24
        else:
            imm24 = (rel_off >> 2) & 0x00FFFFFF
            inst = (inst & 0xFF000000) | imm24
        struct.pack_into("<I", data, reloc.offset, inst)
    return bytes(data)

def create_emulator() -> Uc:
    uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    try:
        uc.ctl_set_cpu_model(UC_CPU_ARM_11MPCORE)
    except Exception:
        pass
    uc.mem_map(CODE_BASE, CODE_SIZE, UC_PROT_READ | UC_PROT_EXEC | UC_PROT_WRITE)
    uc.mem_map(STACK_BASE, STACK_SIZE, UC_PROT_READ | UC_PROT_WRITE)
    uc.mem_map(0x10000000, 0x00100000, UC_PROT_READ | UC_PROT_WRITE)
    uc.mem_write(CODE_BASE, ORIG_DATA)
    if RODATA_BYTES:
        uc.mem_write(RODATA_ADDR, RODATA_BYTES)
    try:
        uc.reg_write(UC_ARM_REG_C1_C0_2, 0x00F00000)
        uc.reg_write(UC_ARM_REG_FPEXC, 0x40000000)
    except Exception:
        pass
    return uc

def setup_call(uc: Uc, addr: int, r0=0, r1=0, r2=0, r3=0, stack_args=None, vfp_args=None):
    uc.reg_write(UC_ARM_REG_R0, r0)
    uc.reg_write(UC_ARM_REG_R1, r1)
    uc.reg_write(UC_ARM_REG_R2, r2)
    uc.reg_write(UC_ARM_REG_R3, r3)
    if vfp_args:
        vfp_regs = [
            UC_ARM_REG_S0, UC_ARM_REG_S1, UC_ARM_REG_S2, UC_ARM_REG_S3,
            UC_ARM_REG_S4, UC_ARM_REG_S5, UC_ARM_REG_S6, UC_ARM_REG_S7,
            UC_ARM_REG_S8, UC_ARM_REG_S9
        ]
        for reg, val in zip(vfp_regs, vfp_args):
            uc.reg_write(reg, struct.unpack('<I', struct.pack('<f', val))[0])
    sp = STACK_TOP
    if stack_args:
        sp -= len(stack_args) * 4
        for i, val in enumerate(stack_args):
            uc.mem_write(sp + i * 4, struct.pack("<I", val & 0xFFFFFFFF))
    uc.reg_write(UC_ARM_REG_SP, sp)
    uc.reg_write(UC_ARM_REG_LR, 0xDEADBEE0)
    uc.reg_write(UC_ARM_REG_PC, addr)

def run_until_ret(uc: Uc, ret_addr=0xDEADBEE0, max_ins=200000):
    count = 0
    while True:
        pc = uc.reg_read(UC_ARM_REG_PC)
        if pc == ret_addr:
            break
        if count >= max_ins:
            raise RuntimeError(f"Execution exceeded max instructions ({max_ins}), PC=0x{pc:08x}")
        try:
            uc.emu_start(pc, ret_addr, timeout=0, count=1000)
        except Exception as e:
            curr_pc = uc.reg_read(UC_ARM_REG_PC)
            print(f"ERROR at PC=0x{curr_pc:08x}: {e}")
            raise
        count += 1000


# ==============================================================================
# Candidate 1: ui_func_002b6030 (0x002b6030, 572 B)
# ==============================================================================

def test_ui_func_002b6030():
    comp_body, relocs = compile_function("ui_func_002b6030")
    STUB_138E44 = 0x00480000
    STUB_2ABAB0 = 0x00480010
    STUB_2BCF58 = 0x00480020

    staged_comp = stage_body(comp_body, relocs, 0x002b6030, {
        "func_00138e44": STUB_138E44,
        "ui_func_002abab0": STUB_2ABAB0,
        "ui_func_002bcf58": STUB_2BCF58,
    }, "ui_func_002b6030")

    def install_stubs(uc: Uc):
        def hook_code(uc_engine, address, size, user_data):
            lr = uc_engine.reg_read(UC_ARM_REG_LR)
            r0 = uc_engine.reg_read(UC_ARM_REG_R0)
            r1 = uc_engine.reg_read(UC_ARM_REG_R1)
            r2 = uc_engine.reg_read(UC_ARM_REG_R2)
            if address in (0x00138e44, STUB_138E44):
                # returns r0 (which is out)
                uc_engine.reg_write(UC_ARM_REG_PC, lr)
            elif address in (0x002abab0, STUB_2ABAB0):
                # r0 = obj, r1 = cmd_buf, r2 = tag. Writes tag to cmd_buf and returns cmd_buf + 8
                cmd_buf = r1
                uc_engine.mem_write(cmd_buf, struct.pack('<II', r2, 0xAAAA0000))
                uc_engine.reg_write(UC_ARM_REG_R0, cmd_buf + 8)
                uc_engine.reg_write(UC_ARM_REG_PC, lr)
            elif address in (0x002bcf58, STUB_2BCF58):
                # memcpy(dest=r0, src=r1, size=r2)
                if r2 > 0:
                    data = uc_engine.mem_read(r1, r2)
                    uc_engine.mem_write(r0, bytes(data))
                uc_engine.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(unicorn.UC_HOOK_CODE, hook_code)

    cases = [
        ("r1_idx_neg", -1, 0, 0),
        ("r1_idx_0", 0, 0, 0),
        ("r1_idx_2", 2, 0, 0),
        ("b298_is_3", 0, 3, 1),
        ("b298_is_0", 0, 0, 1),
    ]

    for cname, r1_idx, b298, r0_idx in cases:
        def run_variant(code_bytes, entry_addr):
            uc = create_emulator()
            uc.mem_write(entry_addr, code_bytes)
            install_stubs(uc)

            OBJ_ADDR = 0x10020000
            OUT_ADDR = 0x10040000

            obj_buf = bytearray(0x20000)
            struct.pack_into('<i', obj_buf, 0, r0_idx)
            struct.pack_into('<i', obj_buf, 4, r1_idx)
            obj_buf[0x298] = b298
            struct.pack_into('<I', obj_buf, 0x8c, 0x1111)
            struct.pack_into('<I', obj_buf, 0x90, 0x2222)
            struct.pack_into('<I', obj_buf, 0x294, 0x3333)
            struct.pack_into('<I', obj_buf, 0x29c, 0x4444)
            struct.pack_into('<I', obj_buf, 0x2a0, 0x5555)
            struct.pack_into('<I', obj_buf, 0x364, 4) # 4 words for last copy

            # counts at 0x12868
            for i in range(5):
                struct.pack_into('<I', obj_buf, 0x12868 + i * 4, 3)

            # fill data in src buffers
            for i in range(100):
                struct.pack_into('<I', obj_buf, 0x368 + i * 4, 0xAA00 + i)
                struct.pack_into('<I', obj_buf, 0x368 + 293 * 8 + i * 4, 0xBB00 + i)
                struct.pack_into('<I', obj_buf, 0x368 + 2 * 293 * 8 + i * 4, 0xCC00 + i)
                struct.pack_into('<I', obj_buf, 0x2a4 + i * 4, 0xDD00 + i)

            uc.mem_write(OBJ_ADDR, bytes(obj_buf))

            setup_call(uc, entry_addr, OBJ_ADDR, OUT_ADDR)
            run_until_ret(uc)

            ret_ptr = uc.reg_read(UC_ARM_REG_R0)
            out_bytes = uc.mem_read(OUT_ADDR, ret_ptr - OUT_ADDR)
            return (ret_ptr, out_bytes)

        orig_res = run_variant(load_original_bytes(0x002b6030, 572), 0x002b6030)
        comp_res = run_variant(staged_comp, 0x002b6030)

        assert orig_res[0] == comp_res[0], f"{cname}: ret mismatch (orig={hex(orig_res[0])}, comp={hex(comp_res[0])})"
        assert orig_res[1] == comp_res[1], f"{cname}: output buffer mismatch"

    print(f"PASS: ui_func_002b6030 (all {len(cases)} cases passed)")


# ==============================================================================
# Candidate 2: ui_func_002b8104 (0x002b8104, 1056 B)
# ==============================================================================

def test_ui_func_002b8104():
    comp_body, relocs = compile_function("ui_func_002b8104")
    STUB_2A9414 = 0x00480030
    staged_comp = stage_body(comp_body, relocs, 0x002b8104, {
        "func_002a9414": STUB_2A9414
    }, "ui_func_002b8104")

    # Map tables at 0x004e31a0 and 0x004e35a0
    # Note: 0x004e0000 is inside CODE_BASE..CODE_BASE+CODE_SIZE! (0x00100000 .. 0x00500000)
    # So 0x004e31a0 and 0x004e35a0 are already populated from code.bin!

    cases = [
        ("normal_quad", 10.0, 20.0, 100.0, 50.0, 0.0, 0.0, 1.0, 1.0, 0.5, [0x11223344, 0x55667788, 0x99AABBCC, 0xDDEEFF00]),
        ("negative_coords", -10.0, -20.0, 50.0, 50.0, 0.5, 0.5, 0.25, 0.25, 0.0, [0xFFFFFFFF, 0x00000000, 0x12345678, 0x87654321]),
        ("zeros", 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, [0, 0, 0, 0]),
    ]

    for cname, x, y, w, h, u, v, uw, vh, z, colors in cases:
        def run_variant(code_bytes, entry_addr):
            uc = create_emulator()
            uc.mem_write(entry_addr, code_bytes)
            vtx_calls = []

            def hook_code(uc_engine, address, size, user_data):
                if address in (0x002a9414, STUB_2A9414):
                    lr = uc_engine.reg_read(UC_ARM_REG_LR)
                    p_pos = uc_engine.reg_read(UC_ARM_REG_R0)
                    p_col = uc_engine.reg_read(UC_ARM_REG_R1)
                    p_tex = uc_engine.reg_read(UC_ARM_REG_R2)
                    pos = struct.unpack('<3I', uc_engine.mem_read(p_pos, 12))
                    col = struct.unpack('<3I', uc_engine.mem_read(p_col, 12))
                    tex = struct.unpack('<2I', uc_engine.mem_read(p_tex, 8))
                    vtx_calls.append((pos, col, tex))
                    uc_engine.reg_write(UC_ARM_REG_PC, lr)

            uc.hook_add(unicorn.UC_HOOK_CODE, hook_code)

            setup_call(uc, entry_addr, r0=colors[0], r1=colors[1], r2=colors[2], r3=colors[3], vfp_args=[x, y, w, h, u, v, uw, vh, z])
            run_until_ret(uc)
            return vtx_calls

        orig_res = run_variant(load_original_bytes(0x002b8104, 1056), 0x002b8104)
        comp_res = run_variant(staged_comp, 0x002b8104)

        assert orig_res == comp_res, f"{cname}: vertex calls mismatch (orig={orig_res}, comp={comp_res})"

    print(f"PASS: ui_func_002b8104 (all {len(cases)} cases passed)")


# ==============================================================================
# Candidate 3: func_002bb5c4 (0x002bb5c4, 68 B)
# ==============================================================================

def test_func_002bb5c4():
    comp_body, relocs = compile_function("func_002bb5c4")
    staged_comp = stage_body(comp_body, relocs, 0x002bb5c4, {}, "func_002bb5c4")

    cases = [
        ("success_call", 0x1234, 0x42, 0x5678, 0),
        ("error_call", 0x9999, 0x00, 0x0000, 0x80000001), # bmi triggered
    ]

    for cname, in_val, resp_b2, resp_r0, svc_ret in cases:
        def run_variant(code_bytes, entry_addr):
            uc = create_emulator()
            uc.mem_write(entry_addr, code_bytes)

            TLS_ADDR = 0x10020000
            uc.reg_write(UC_ARM_REG_C13_C0_3, TLS_ADDR)

            # Global handle at 0x004656b0
            uc.mem_write(0x004656b0, struct.pack('<I', 0xDEAD0001))

            OUT_PTR = 0x10030000
            uc.mem_write(OUT_PTR, b'\x00')

            def hook_intr(uc_engine, intno, user_data):
                if intno == 2:
                    pc = uc_engine.reg_read(UC_ARM_REG_PC)
                    ins = struct.unpack('<I', uc_engine.mem_read(pc - 4, 4))[0]
                    if (ins & 0x00FFFFFF) == 0x32:
                        uc_engine.reg_write(UC_ARM_REG_R0, svc_ret)
                        if svc_ret == 0:
                            # write cmdbuf responses
                            uc_engine.mem_write(TLS_ADDR + 0x88, struct.pack('<I', resp_b2))
                            uc_engine.mem_write(TLS_ADDR + 0x84, struct.pack('<I', resp_r0))

            uc.hook_add(UC_HOOK_INTR, hook_intr)

            setup_call(uc, entry_addr, in_val, OUT_PTR)
            run_until_ret(uc)

            ret = uc.reg_read(UC_ARM_REG_R0)
            out_b = uc.mem_read(OUT_PTR, 1)[0]
            cmdbuf = struct.unpack('<3I', uc.mem_read(TLS_ADDR + 0x80, 12))
            return (ret, out_b, cmdbuf)

        orig_res = run_variant(load_original_bytes(0x002bb5c4, 68), 0x002bb5c4)
        comp_res = run_variant(staged_comp, 0x002bb5c4)

        assert orig_res == comp_res, f"{cname}: mismatch (orig={orig_res}, comp={comp_res})"

    print(f"PASS: func_002bb5c4 (all {len(cases)} cases passed)")


# ==============================================================================
# Candidate 4: engine_func_002c42fc (0x002c42fc, 100 B)
# ==============================================================================

def test_engine_func_002c42fc():
    comp_body, relocs = compile_function("engine_func_002c42fc")
    staged_comp = stage_body(comp_body, relocs, 0x002c42fc, {}, "engine_func_002c42fc")

    cases = [
        ("svc_control_memory_alloc", 0x10000000, 0x20000000, 0x1000, 3, 7),
        ("svc_control_memory_free", 0x10000000, 0x20000000, 0x1000, 1, 0),
    ]

    for cname, a0, a1, sz, op, perm in cases:
        def run_variant(code_bytes, entry_addr):
            uc = create_emulator()
            uc.mem_write(entry_addr, code_bytes)

            OUT_ADDR = 0x10030000
            uc.mem_write(OUT_ADDR, struct.pack('<I', 0))

            def hook_intr(uc_engine, intno, user_data):
                if intno == 2:
                    pc = uc_engine.reg_read(UC_ARM_REG_PC)
                    ins = struct.unpack('<I', uc_engine.mem_read(pc - 4, 4))[0]
                    if (ins & 0x00FFFFFF) == 0x25:
                        uc_engine.reg_write(UC_ARM_REG_R0, 0) # Result
                        uc_engine.reg_write(UC_ARM_REG_R1, 0x08001000) # out_addr

            uc.hook_add(UC_HOOK_INTR, hook_intr)

            setup_call(uc, entry_addr, OUT_ADDR, a0, a1, sz, stack_args=[op, perm])
            run_until_ret(uc)

            ret = uc.reg_read(UC_ARM_REG_R0)
            written = struct.unpack('<I', uc.mem_read(OUT_ADDR, 4))[0] if OUT_ADDR else 0
            return (ret, written)

        orig_res = run_variant(load_original_bytes(0x002c42fc, 36), 0x002c42fc)
        comp_res = run_variant(staged_comp, 0x002c42fc)

        assert orig_res == comp_res, f"{cname}: mismatch (orig={orig_res}, comp={comp_res})"

    # Also test second function engine_func_002c4320
    comp_body2, relocs2 = compile_function("engine_func_002c4320")
    STUB_2C57C4 = 0x00480040
    STUB_2C5624 = 0x00480050
    staged_comp2 = stage_body(comp_body2, relocs2, 0x002c4320, {
        "engine_func_002c57c4": STUB_2C57C4,
        "engine_func_002c5624": STUB_2C5624,
    }, "engine_func_002c4320")

    for new_val in [0, 1, -1]:
        def run_variant2(code_bytes, entry_addr):
            uc = create_emulator()
            uc.mem_write(entry_addr, code_bytes)
            calls = []

            def hook_code(uc_engine, address, size, user_data):
                lr = uc_engine.reg_read(UC_ARM_REG_LR)
                r0 = uc_engine.reg_read(UC_ARM_REG_R0)
                if address in (0x002c57c4, STUB_2C57C4):
                    calls.append(('2c57c4', r0))
                    uc_engine.reg_write(UC_ARM_REG_PC, lr)
                elif address in (0x002c5624, STUB_2C5624):
                    calls.append(('2c5624', r0))
                    uc_engine.reg_write(UC_ARM_REG_PC, lr)

            uc.hook_add(unicorn.UC_HOOK_CODE, hook_code)
            uc.mem_write(0x00465198, struct.pack('<b', 42))

            setup_call(uc, entry_addr, new_val)
            run_until_ret(uc)

            ret = struct.unpack('<b', struct.pack('<B', uc.reg_read(UC_ARM_REG_R0) & 0xFF))[0]
            val_after = struct.unpack('<b', uc.mem_read(0x00465198, 1))[0]
            return (ret, val_after, calls)

        orig_res = run_variant2(load_original_bytes(0x002c4320, 64), 0x002c4320)
        comp_res = run_variant2(staged_comp2, 0x002c4320)

        assert orig_res == comp_res, f"val={new_val}: mismatch (orig={orig_res}, comp={comp_res})"

    print("PASS: engine_func_002c42fc & engine_func_002c4320 (all cases passed)")


# ==============================================================================
# Candidate 5: script_vm_func_002f364c (0x002f364c, 624 B)
# ==============================================================================

def test_script_vm_func_002f364c():
    comp_body, relocs = compile_function("script_vm_func_002f364c")
    STUB_2C2B1C = 0x00480060
    STUB_24F7E8 = 0x00480070
    STUB_24F7A8 = 0x00480080
    STUB_248320 = 0x00480090
    STUB_25B8A8 = 0x004800A0
    STUB_248F6C = 0x004800B0
    STUB_27F094 = 0x004800C0
    STUB_2C0BCC = 0x004800D0
    STUB_1FC270 = 0x004800E0

    staged_comp = stage_body(comp_body, relocs, 0x002f364c, {
        "engine_func_002c2b1c": STUB_2C2B1C,
        "script_vm_func_0024f7e8": STUB_24F7E8,
        "camp_func_0024f7a8": STUB_24F7A8,
        "script_vm_func_00248320": STUB_248320,
        "script_vm_func_0025b8a8": STUB_25B8A8,
        "engine_func_00248f6c": STUB_248F6C,
        "engine_func_0027f094": STUB_27F094,
        "engine_func_002c0bcc": STUB_2C0BCC,
        "script_vm_func_001fc270": STUB_1FC270,
    }, "script_vm_func_002f364c")

    CTX_ADDR = 0x10020000
    REC_POOL = 0x10030000

    cases = [
        ("total_zero", 0, 10, 10),
        ("map_mismatch", 1, 10, 20),
        ("map_match_normal", 1, 10, 10),
    ]

    for cname, total, val20, cur_map in cases:
        def run_variant(code_bytes, entry_addr):
            uc = create_emulator()
            uc.mem_write(entry_addr, code_bytes)
            calls_log = []

            def hook_code(uc_engine, address, size, user_data):
                lr = uc_engine.reg_read(UC_ARM_REG_LR)
                r0 = uc_engine.reg_read(UC_ARM_REG_R0)
                if address in (0x002c2b1c, STUB_2C2B1C):
                    uc_engine.reg_write(UC_ARM_REG_R0, CTX_ADDR)
                    uc_engine.reg_write(UC_ARM_REG_PC, lr)
                elif address in (0x0024f7e8, STUB_24F7E8):
                    uc_engine.reg_write(UC_ARM_REG_R0, total)
                    uc_engine.reg_write(UC_ARM_REG_PC, lr)
                elif address in (0x0024f7a8, STUB_24F7A8):
                    uc_engine.reg_write(UC_ARM_REG_R0, REC_POOL)
                    uc_engine.reg_write(UC_ARM_REG_PC, lr)
                elif address in (0x00248320, STUB_248320):
                    uc_engine.reg_write(UC_ARM_REG_R0, 2)
                    uc_engine.reg_write(UC_ARM_REG_PC, lr)
                elif address in (0x0025b8a8, STUB_25B8A8):
                    uc_engine.reg_write(UC_ARM_REG_R0, REC_POOL + 0x100 + r0 * 0x30)
                    uc_engine.reg_write(UC_ARM_REG_PC, lr)
                elif address in (0x00248f6c, STUB_248F6C):
                    uc_engine.reg_write(UC_ARM_REG_R0, 3)
                    uc_engine.reg_write(UC_ARM_REG_PC, lr)
                elif address in (0x0027f094, STUB_27F094):
                    uc_engine.reg_write(UC_ARM_REG_R0, REC_POOL + 0x200 + r0 * 0x20)
                    uc_engine.reg_write(UC_ARM_REG_PC, lr)
                elif address in (0x002c0bcc, STUB_2C0BCC):
                    uc_engine.reg_write(UC_ARM_REG_R0, 0)
                    uc_engine.reg_write(UC_ARM_REG_PC, lr)
                elif address in (0x001fc270, STUB_1FC270):
                    calls_log.append(('1fc270', r0))
                    uc_engine.reg_write(UC_ARM_REG_PC, lr)

            uc.hook_add(unicorn.UC_HOOK_CODE, hook_code)

            # Global current_map at 0x0049f91c
            uc.mem_write(0x0049f91c, struct.pack('<i', cur_map))

            ctx_buf = bytearray(0x2000)
            uc.mem_write(CTX_ADDR, bytes(ctx_buf))

            # REC_POOL: val20 at 0x20, val28=0 at 0x28, val26=2 at 0x26
            rec_buf = bytearray(0x40)
            struct.pack_into('<h', rec_buf, 0x20, val20)
            struct.pack_into('<h', rec_buf, 0x28, 0)
            struct.pack_into('<H', rec_buf, 0x26, 2)
            uc.mem_write(REC_POOL, bytes(rec_buf))

            # 25b8a8 records: 0x20 = 0, 0x26 = val20, 0x24 = 5 + r0
            for i in range(2):
                b = bytearray(0x30)
                struct.pack_into('<i', b, 0x20, 0)
                b[0x26] = val20 & 0xFF
                struct.pack_into('<h', b, 0x24, 5 + i)
                uc.mem_write(REC_POOL + 0x100 + i * 0x30, bytes(b))

            # 27f094 items: b0 = val20, b1 = 0, b0b = 0 or 6
            for i in range(3):
                b = bytearray(0x20)
                b[0] = val20 & 0xFF
                b[1] = 0 # matches r6 = 0
                b[0xb] = 0 if i == 0 else 6
                uc.mem_write(REC_POOL + 0x200 + i * 0x20, bytes(b))

            setup_call(uc, entry_addr)
            run_until_ret(uc)

            ctx_out = uc.mem_read(CTX_ADDR, 0x2000)
            return (ctx_out, calls_log)

        orig_res = run_variant(load_original_bytes(0x002f364c, 624), 0x002f364c)
        comp_res = run_variant(staged_comp, 0x002f364c)

        assert orig_res[0] == comp_res[0], f"{cname}: ctx mismatch"
        assert orig_res[1] == comp_res[1], f"{cname}: calls mismatch"

    print(f"PASS: script_vm_func_002f364c (all {len(cases)} cases passed)")


if __name__ == "__main__":
    test_ui_func_002b6030()
    test_ui_func_002b8104()
    test_func_002bb5c4()
    test_engine_func_002c42fc()
    test_script_vm_func_002f364c()
    print("\nALL 5 CANDIDATES IN PART 18 PASSED DIFFERENTIAL VERIFICATION!")
