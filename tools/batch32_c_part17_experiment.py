#!/usr/bin/env python3
"""Differential test runner for leaf_batch32_c Part 17 candidates against code.bin.

Tests:
  - 0x002dad3c: camp_func_002dad3c (592 B)
  - 0x002e3684: camp_func_002e3684 (412 B)
  - 0x002eb174: func_002eb174 (60 B)
  - 0x002ece08: script_vm_func_002ece08 (388 B)
  - 0x002eff60: camp_func_002eff60 (512 B)
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
SOURCE = ROOT / "src" / "engine" / "leaf_batch32_c.cpp"

CODE_BASE = 0x00100000
CODE_SIZE = 0x00400000
STACK_BASE = 0x0FFF0000
STACK_SIZE = 0x00010000
STACK_TOP = STACK_BASE + STACK_SIZE - 0x1000

BUILD_DIR = ROOT / "build" / "batch32_c_part17"

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

def setup_call(uc: Uc, addr: int, r0=0, r1=0, r2=0, r3=0, stack_args=None):
    uc.reg_write(UC_ARM_REG_R0, r0)
    uc.reg_write(UC_ARM_REG_R1, r1)
    uc.reg_write(UC_ARM_REG_R2, r2)
    uc.reg_write(UC_ARM_REG_R3, r3)
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
# Candidate 1: camp_func_002dad3c (0x002dad3c, 592 B)
# ==============================================================================

def test_camp_func_002dad3c():
    comp_body, relocs = compile_function("camp_func_002dad3c")
    STUB_2840B8 = 0x00480000
    staged_comp = stage_body(comp_body, relocs, 0x002dad3c, {
        "camp_func_002840b8": STUB_2840B8
    }, "camp_func_002dad3c")

    # Item descriptor buffer: item_id -> pointer
    # At STUB_2840B8: read r0 (id). Return table[id]
    ITEM_TBL_BASE = 0x10020000

    def install_stub(uc: Uc):
        def hook_code(uc_engine, address, size, user_data):
            if address in (0x002840b8, STUB_2840B8):
                item_id = uc_engine.reg_read(UC_ARM_REG_R0)
                ptr = struct.unpack('<I', uc_engine.mem_read(ITEM_TBL_BASE + item_id * 4, 4))[0]
                uc_engine.reg_write(UC_ARM_REG_R0, ptr)
                uc_engine.reg_write(UC_ARM_REG_PC, uc_engine.reg_read(UC_ARM_REG_LR))
        uc.hook_add(unicorn.UC_HOOK_CODE, hook_code)

    cases = [
        ("no_items", [100, 50, 10, 12, 14, 16, 18], [], 0),
        ("normal_bonuses", [200, 100, 20, 20, 20, 20, 20], [1, 2], 2),
        ("cat_ignored", [200, 100, 20, 20, 20, 20, 20], [3], 1),
        ("exact_scale_plus1", [10, 10, 5, 5, 5, 5, 5], [4], 1),
        ("cap_9999_hp_mp", [8000, 8000, 50, 50, 50, 50, 50], [5], 1),
        ("cap_999_stats", [100, 100, 950, 950, 950, 950, 950], [5], 1),
        ("null_item_ptr", [100, 100, 10, 10, 10, 10, 10], [99], 1),
    ]

    ITEM_BUF = 0x10030000
    # Setup mock items
    # item 1: cat=10, b24=1 (+10% hp), b25=2 (+20% mp), b28=5(st), b29=6(dx), b2a=7(ma), b2b=8(ag), b2c=9(lu)
    # item 2: cat=10, b24=0, b25=1 (+10% mp), b28=2(st), b29=2(dx), b2a=2(ma), b2b=2(ag), b2c=2(lu)
    # item 3: cat=9 (ignored!), b24=5, b28=50
    # item 4: cat=10, b24=1 (+10% hp on 10 hp -> 11, but 10*110/100 = 11, wait: scale 105: not possible with b24*10 unless scale_hp > 100 and new_hp == hp: hp=9, scale=110 -> 9*110/100 = 9 -> new_hp=10)
    # item 5: cat=10, b24=50 (+500% hp), b25=50, b28=100, b29=100, b2a=100, b2b=100, b2c=100

    item_data = {}
    def make_item(cat, b24, b25, b28, b29, b2a, b2b, b2c):
        buf = bytearray(0x40)
        # category: (val >> 6) == cat -> val = cat << 6
        struct.pack_into('<I', buf, 0x38, cat << 6)
        buf[0x24] = b24
        buf[0x25] = b25
        buf[0x28] = b28
        buf[0x29] = b29
        buf[0x2a] = b2a
        buf[0x2b] = b2b
        buf[0x2c] = b2c
        return bytes(buf)

    item_data[1] = make_item(10, 1, 2, 5, 6, 7, 8, 9)
    item_data[2] = make_item(10, 0, 1, 2, 2, 2, 2, 2)
    item_data[3] = make_item(9, 5, 5, 50, 50, 50, 50, 50) # not cat 10
    item_data[4] = make_item(10, 1, 1, 0, 0, 0, 0, 0) # scale 110
    item_data[5] = make_item(10, 50, 50, 100, 100, 100, 100, 100)

    for cname, initial_stats, item_list, count in cases:
        def run_variant(code_bytes, entry_addr):
            uc = create_emulator()
            uc.mem_write(entry_addr, code_bytes)
            install_stub(uc)

            # write item tbl
            for iid in range(100):
                uc.mem_write(ITEM_TBL_BASE + iid * 4, struct.pack('<I', 0))
            for iid, data in item_data.items():
                addr = ITEM_BUF + iid * 0x40
                uc.mem_write(addr, data)
                uc.mem_write(ITEM_TBL_BASE + iid * 4, struct.pack('<I', addr))

            STATS_ADDR = 0x10005000
            for idx, s in enumerate(initial_stats):
                uc.mem_write(STATS_ADDR + idx * 2, struct.pack('<h', s))

            ITEMS_ADDR = 0x10006000
            for idx, item in enumerate(item_list):
                uc.mem_write(ITEMS_ADDR + idx * 2, struct.pack('<H', item))

            setup_call(uc, entry_addr, STATS_ADDR, ITEMS_ADDR, count)
            run_until_ret(uc)

            res = [struct.unpack('<h', uc.mem_read(STATS_ADDR + i * 2, 2))[0] for i in range(7)]
            return res

        orig_res = run_variant(load_original_bytes(0x002dad3c, 592), 0x002dad3c)
        comp_res = run_variant(staged_comp, 0x002dad3c)
        assert orig_res == comp_res, f"{cname}: mismatch (orig={orig_res}, comp={comp_res})"

    print(f"PASS: camp_func_002dad3c (all {len(cases)} cases passed)")


# ==============================================================================
# Candidate 2: camp_func_002e3684 (0x002e3684, 412 B)
# ==============================================================================

def test_camp_func_002e3684():
    comp_body, relocs = compile_function("camp_func_002e3684")
    STUB_2A8A08 = 0x00480010
    STUB_2C4450 = 0x00480020
    STUB_2B0824 = 0x00480030
    STUB_2A89E4 = 0x00480040

    staged_comp = stage_body(comp_body, relocs, 0x002e3684, {
        "camp_func_002a8a08": STUB_2A8A08,
        "camp_func_002c4450": STUB_2C4450,
        "camp_func_002b0824": STUB_2B0824,
        "camp_func_002a89e4": STUB_2A89E4,
    }, "camp_func_002e3684")

    CTX_ADDR = 0x10020000
    PARTY_CTX_ADDR = 0x10030000
    DEMON_POOL = 0x10040000

    def install_stubs(uc: Uc, calls_log):
        def hook_code(uc_engine, address, size, user_data):
            if address in (0x002a8a08, STUB_2A8A08):
                uc_engine.reg_write(UC_ARM_REG_R0, PARTY_CTX_ADDR)
                uc_engine.reg_write(UC_ARM_REG_PC, uc_engine.reg_read(UC_ARM_REG_LR))
            elif address in (0x002c4450, STUB_2C4450):
                calls_log.append(('2c4450', uc_engine.reg_read(UC_ARM_REG_R0), uc_engine.reg_read(UC_ARM_REG_R1), uc_engine.reg_read(UC_ARM_REG_R2)))
                uc_engine.reg_write(UC_ARM_REG_PC, uc_engine.reg_read(UC_ARM_REG_LR))
            elif address in (0x002b0824, STUB_2B0824):
                demon_id = uc_engine.reg_read(UC_ARM_REG_R0)
                # target_val at DEMON_POOL + demon_id * 0x50 + 0x46
                addr = DEMON_POOL + demon_id * 0x50
                uc_engine.reg_write(UC_ARM_REG_R0, addr)
                uc_engine.reg_write(UC_ARM_REG_PC, uc_engine.reg_read(UC_ARM_REG_LR))
            elif address in (0x002a89e4, STUB_2A89E4):
                slot = uc_engine.reg_read(UC_ARM_REG_R0)
                addr = DEMON_POOL + 0x1000 + slot * 0x50
                uc_engine.reg_write(UC_ARM_REG_R0, addr)
                uc_engine.reg_write(UC_ARM_REG_PC, uc_engine.reg_read(UC_ARM_REG_LR))
        uc.hook_add(unicorn.UC_HOOK_CODE, hook_code)

    cases = [
        ("count_0", 0, [], [], []),
        ("party_match", 1, [5], [5, -1, -1], [10] * 24),
        ("stock_match", 1, [8], [-1, -1, -1], [8] + [10] * 23),
        ("no_match", 1, [7], [1, 2, 3], [10] * 24),
        ("negative_slots", 1, [-1], [-1, -1, -1], [-1] * 24),
    ]

    for cname, count, id_list, party_slots, stock_slots in cases:
        def run_variant(code_bytes, entry_addr):
            uc = create_emulator()
            uc.mem_write(entry_addr, code_bytes)
            calls_log = []
            install_stubs(uc, calls_log)

            # Global context pointer at 0x0043dcf0
            uc.mem_write(0x0043dcf0, struct.pack('<I', CTX_ADDR))

            # Initialize CTX_ADDR memory
            ctx_buf = bytearray(0x1000)
            struct.pack_into('<i', ctx_buf, 0xb3c, count)
            for idx, cid in enumerate(id_list):
                struct.pack_into('<i', ctx_buf, 0xb34 + idx * 4, cid)

            # setup widget pointers ctx + 0x6c8 (4 party widgets), ctx + 0x6d8 (24 stock widgets)
            WIDGET_BASE = 0x10050000
            for i in range(4):
                struct.pack_into('<I', ctx_buf, 0x6c8 + i * 4, WIDGET_BASE + i * 0x30)
                uc.mem_write(WIDGET_BASE + i * 0x30 + 0x28, b'\x05')
            for i in range(24):
                struct.pack_into('<I', ctx_buf, 0x6d8 + i * 4, WIDGET_BASE + 0x200 + i * 0x30)
                uc.mem_write(WIDGET_BASE + 0x200 + i * 0x30 + 0x28, b'\x05')

            # setup stock slots ctx + 0x738 + i*8
            for i, sval in enumerate(stock_slots):
                struct.pack_into('<i', ctx_buf, 0x738 + i * 8, sval)

            uc.mem_write(CTX_ADDR, bytes(ctx_buf))

            # Setup party ctx: party slots at party_ctx + 0x9108 + r4
            party_buf = bytearray(0x9200)
            for i, pval in enumerate(party_slots):
                party_buf[0x9108 + i] = pval & 0xFF
            uc.mem_write(PARTY_CTX_ADDR, bytes(party_buf))

            # Setup demon species values at DEMON_POOL + id*0x50 + 0x46
            # Make id species == id (so id 5 has species 0x55, id 8 has species 0x88, etc.)
            for d in range(20):
                uc.mem_write(DEMON_POOL + d * 0x50 + 0x46, struct.pack('<H', d * 11))
                uc.mem_write(DEMON_POOL + 0x1000 + d * 0x50 + 0x46, struct.pack('<H', d * 11))

            setup_call(uc, entry_addr)
            run_until_ret(uc)

            ctx_out = uc.mem_read(CTX_ADDR, 0x1000)
            widgets_out = uc.mem_read(WIDGET_BASE, 0x800)
            return (ctx_out, widgets_out, calls_log)

        orig_res = run_variant(load_original_bytes(0x002e3684, 412), 0x002e3684)
        comp_res = run_variant(staged_comp, 0x002e3684)

        assert orig_res[0] == comp_res[0], f"{cname}: ctx mismatch"
        assert orig_res[1] == comp_res[1], f"{cname}: widgets mismatch"
        assert orig_res[2] == comp_res[2], f"{cname}: calls mismatch"

    print(f"PASS: camp_func_002e3684 (all {len(cases)} cases passed)")


# ==============================================================================
# Candidate 3: func_002eb174 (0x002eb174, 60 B)
# ==============================================================================

def test_func_002eb174():
    comp_body, relocs = compile_function("func_002eb174")
    STUB_39B054 = 0x00480050
    staged_comp = stage_body(comp_body, relocs, 0x002eb174, {
        "func_0039b054": STUB_39B054
    }, "func_002eb174")

    cases = [
        ("null_obj", 0, 100),
        ("normal_obj", 0x10020000, 0x1234),
        ("zero_arg", 0x10020000, 0),
        ("neg_arg", 0x10020000, -1),
    ]

    for cname, obj_ptr, arg0 in cases:
        def run_variant(code_bytes, entry_addr):
            uc = create_emulator()
            uc.mem_write(entry_addr, code_bytes)
            calls = []

            def hook_code(uc_engine, address, size, user_data):
                if address in (0x0039b054, STUB_39B054):
                    r0 = uc_engine.reg_read(UC_ARM_REG_R0)
                    r1 = uc_engine.reg_read(UC_ARM_REG_R1)
                    r2 = uc_engine.reg_read(UC_ARM_REG_R2)
                    r3 = uc_engine.reg_read(UC_ARM_REG_R3)
                    sp = uc_engine.reg_read(UC_ARM_REG_SP)
                    stack = struct.unpack('<5I', uc_engine.mem_read(sp, 20))
                    calls.append((r0, r1, r2, r3, stack))
                    uc_engine.reg_write(UC_ARM_REG_PC, uc_engine.reg_read(UC_ARM_REG_LR))

            uc.hook_add(unicorn.UC_HOOK_CODE, hook_code)

            # Global singleton pointer at 0x0044cdf0
            uc.mem_write(0x0044cdf0, struct.pack('<I', obj_ptr))
            # Also set r12 = obj_ptr for the original ARM slice artifact
            uc.reg_write(UC_ARM_REG_R12, obj_ptr)

            setup_call(uc, entry_addr, arg0)
            run_until_ret(uc)
            return calls

        orig_res = run_variant(load_original_bytes(0x002eb174, 60), 0x002eb174)
        comp_res = run_variant(staged_comp, 0x002eb174)

        assert orig_res == comp_res, f"{cname}: mismatch (orig={orig_res}, comp={comp_res})"

    print(f"PASS: func_002eb174 (all {len(cases)} cases passed)")


# ==============================================================================
# Candidate 4: script_vm_func_002ece08 (0x002ece08, 388 B)
# ==============================================================================

def test_script_vm_func_002ece08():
    comp_body, relocs = compile_function("script_vm_func_002ece08")
    STUB_2972F8 = 0x00480060
    STUB_2971E4 = 0x00480070
    STUB_2B8B78 = 0x00480080
    STUB_1A06D4 = 0x00480090
    STUB_25485C = 0x004800A0
    STUB_1A9F2C = 0x004800B0
    STUB_254840 = 0x004800C0
    STUB_19DFBC = 0x004800D0
    STUB_2A8A08 = 0x004800E0
    STUB_2A89E4 = 0x004800F0
    STUB_29EE4C = 0x00480100
    STUB_263194 = 0x00480110
    STUB_26BC28 = 0x00480120

    staged_comp = stage_body(comp_body, relocs, 0x002ece08, {
        "scrScriptProcess_func_002972f8": STUB_2972F8,
        "script_vm_func_002971e4": STUB_2971E4,
        "script_vm_func_002b8b78": STUB_2B8B78,
        "CecProcess_func_001a06d4": STUB_1A06D4,
        "camp_func_0025485c": STUB_25485C,
        "engine_func_001a9f2c": STUB_1A9F2C,
        "camp_func_00254840": STUB_254840,
        "script_vm_func_0019dfbc": STUB_19DFBC,
        "camp_func_002a8a08": STUB_2A8A08,
        "camp_func_002a89e4": STUB_2A89E4,
        "camp_func_0029ee4c": STUB_29EE4C,
        "camp_func_00263194": STUB_263194,
        "camp_func_0026bc28": STUB_26BC28,
    }, "script_vm_func_002ece08")

    PARTY_CTX_ADDR = 0x10030000

    def install_stubs(uc: Uc, calls_log, vm_status=2, has_prop=1):
        def hook_code(uc_engine, address, size, user_data):
            lr = uc_engine.reg_read(UC_ARM_REG_LR)
            r0 = uc_engine.reg_read(UC_ARM_REG_R0)
            r1 = uc_engine.reg_read(UC_ARM_REG_R1)
            if address in (0x002972f8, STUB_2972F8):
                calls_log.append(('2972f8', r0, r1))
                uc_engine.reg_write(UC_ARM_REG_R0, 0x77770000)
                uc_engine.reg_write(UC_ARM_REG_PC, lr)
            elif address in (0x002971e4, STUB_2971E4):
                calls_log.append(('2971e4', r0, r1))
                uc_engine.reg_write(UC_ARM_REG_PC, lr)
            elif address in (0x002b8b78, STUB_2B8B78):
                calls_log.append(('2b8b78', r0))
                uc_engine.reg_write(UC_ARM_REG_PC, lr)
            elif address in (0x001a06d4, STUB_1A06D4):
                calls_log.append(('1a06d4',))
                uc_engine.reg_write(UC_ARM_REG_PC, lr)
            elif address in (0x0025485c, STUB_25485C):
                calls_log.append(('25485c',))
                uc_engine.reg_write(UC_ARM_REG_PC, lr)
            elif address in (0x001a9f2c, STUB_1A9F2C):
                calls_log.append(('1a9f2c',))
                uc_engine.reg_write(UC_ARM_REG_PC, lr)
            elif address in (0x00254840, STUB_254840):
                calls_log.append(('254840', r0))
                uc_engine.reg_write(UC_ARM_REG_PC, lr)
            elif address in (0x0019dfbc, STUB_19DFBC):
                calls_log.append(('19dfbc', r0))
                uc_engine.reg_write(UC_ARM_REG_R0, vm_status)
                uc_engine.reg_write(UC_ARM_REG_PC, lr)
            elif address in (0x002a8a08, STUB_2A8A08):
                uc_engine.reg_write(UC_ARM_REG_R0, PARTY_CTX_ADDR)
                uc_engine.reg_write(UC_ARM_REG_PC, lr)
            elif address in (0x002a89e4, STUB_2A89E4):
                calls_log.append(('2a89e4', r0))
                uc_engine.reg_write(UC_ARM_REG_R0, 0x88880000 + r0 * 0x10)
                uc_engine.reg_write(UC_ARM_REG_PC, lr)
            elif address in (0x0029ee4c, STUB_29EE4C):
                calls_log.append(('29ee4c', r0, r1))
                uc_engine.reg_write(UC_ARM_REG_R0, has_prop)
                uc_engine.reg_write(UC_ARM_REG_PC, lr)
            elif address in (0x00263194, STUB_263194):
                calls_log.append(('263194', r0, r1))
                uc_engine.reg_write(UC_ARM_REG_PC, lr)
            elif address in (0x0026bc28, STUB_26BC28):
                calls_log.append(('26bc28',))
                uc_engine.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(unicorn.UC_HOOK_CODE, hook_code)

    cases = [
        ("state0_flag1", 0, 1, 0x11110000, 0x22220000, 2, 1),
        ("state0_flag0", 0, 0, 0x11110000, 0x22220000, 2, 1),
        ("state0_null_r0", 0, 1, 0, 0x22220000, 2, 1),
        ("state1_not_ready", 1, 0, 0, 0, 1, 1),
        ("state1_ready_props", 1, 0, 0, 0, 2, 1),
        ("state1_ready_no_props", 1, 0, 0, 0, 2, 0),
        ("state2_not_ready", 2, 0, 0, 0, 0, 0),
        ("state2_complete", 2, 0, 0, 0, 2, 0),
    ]

    for cname, state, flag, r0_val, r1_val, vm_status, has_prop in cases:
        def run_variant(code_bytes, entry_addr):
            uc = create_emulator()
            uc.mem_write(entry_addr, code_bytes)
            calls_log = []
            install_stubs(uc, calls_log, vm_status, has_prop)

            CTX_ADDR = 0x10020000
            ctx_buf = bytearray(0x1000)
            struct.pack_into('<i', ctx_buf, 0xd38, state)
            struct.pack_into('<i', ctx_buf, 0xd5c, flag)
            struct.pack_into('<I', ctx_buf, 0xcf4, r0_val)
            struct.pack_into('<I', ctx_buf, 0xcf8, r1_val)
            struct.pack_into('<I', ctx_buf, 0xd04, 0x77770000) # handle
            struct.pack_into('<i', ctx_buf, 0xd2c, 0)
            uc.mem_write(CTX_ADDR, bytes(ctx_buf))

            # party slots at PARTY_CTX_ADDR + 0x90f0 + r4
            party_buf = bytearray(0x9200)
            for i in range(24):
                party_buf[0x90f0 + i] = i if (i % 2 == 0) else 0xFF
            uc.mem_write(PARTY_CTX_ADDR, bytes(party_buf))

            setup_call(uc, entry_addr, CTX_ADDR)
            run_until_ret(uc)

            ret = uc.reg_read(UC_ARM_REG_R0)
            ctx_out = uc.mem_read(CTX_ADDR, 0x1000)
            return (ret, ctx_out, calls_log)

        orig_res = run_variant(load_original_bytes(0x002ece08, 388), 0x002ece08)
        comp_res = run_variant(staged_comp, 0x002ece08)

        assert orig_res[0] == comp_res[0], f"{cname}: ret mismatch (orig={orig_res[0]}, comp={comp_res[0]})"
        assert orig_res[1] == comp_res[1], f"{cname}: ctx mismatch"
        assert orig_res[2] == comp_res[2], f"{cname}: calls mismatch"

    print(f"PASS: script_vm_func_002ece08 (all {len(cases)} cases passed)")


# ==============================================================================
# Candidate 5: camp_func_002eff60 (0x002eff60, 512 B)
# ==============================================================================

def test_camp_func_002eff60():
    comp_body, relocs = compile_function("camp_func_002eff60")
    STUB_2A8A08 = 0x00480130
    STUB_29EB58 = 0x00480140
    STUB_29EDFC = 0x00480150
    STUB_2BDAC0 = 0x00480160
    STUB_293A30 = 0x00480170
    STUB_293A84 = 0x00480180

    staged_comp = stage_body(comp_body, relocs, 0x002eff60, {
        "camp_func_002a8a08": STUB_2A8A08,
        "camp_func_0029eb58": STUB_29EB58,
        "camp_func_0029edfc": STUB_29EDFC,
        "camp_func_002bdac0": STUB_2BDAC0,
        "script_vm_func_00293a30": STUB_293A30,
        "camp_func_00293a84": STUB_293A84,
    }, "camp_func_002eff60")

    CTX_ADDR = 0x10020000
    PARTY_CTX_ADDR = 0x10030000

    def install_stubs(uc: Uc, calls_log):
        def hook_code(uc_engine, address, size, user_data):
            lr = uc_engine.reg_read(UC_ARM_REG_LR)
            r0 = uc_engine.reg_read(UC_ARM_REG_R0)
            r1 = uc_engine.reg_read(UC_ARM_REG_R1)
            r2 = uc_engine.reg_read(UC_ARM_REG_R2)
            if address in (0x002a8a08, STUB_2A8A08):
                uc_engine.reg_write(UC_ARM_REG_R0, PARTY_CTX_ADDR)
                uc_engine.reg_write(UC_ARM_REG_PC, lr)
            elif address in (0x0029eb58, STUB_29EB58):
                calls_log.append(('29eb58', r0, r1))
                uc_engine.reg_write(UC_ARM_REG_PC, lr)
            elif address in (0x0029edfc, STUB_29EDFC):
                calls_log.append(('29edfc', r0, r1))
                uc_engine.reg_write(UC_ARM_REG_PC, lr)
            elif address in (0x002bdac0, STUB_2BDAC0):
                calls_log.append(('2bdac0', r0, r1, r2))
                uc_engine.reg_write(UC_ARM_REG_PC, lr)
            elif address in (0x00293a30, STUB_293A30):
                calls_log.append(('293a30', r0, r1))
                uc_engine.reg_write(UC_ARM_REG_PC, lr)
            elif address in (0x00293a84, STUB_293A84):
                calls_log.append(('293a84',))
                uc_engine.reg_write(UC_ARM_REG_PC, lr)

        uc.hook_add(unicorn.UC_HOOK_CODE, hook_code)

    cases = [
        ("invalid_slot", 0, 0, 5, 0, 0, 0),
        ("neg_demon", 1, 0, -1, 0, 0, 0),
        ("flag42_cursor", 1, 0, 5, 5, 1, 0),
        ("p0_no_toggle", 1, 0, 5, 5, 0, 0),
        ("p0_toggle_from_1", 1, 0, 5, 5, 0, 1),
        ("p1_no_toggle", 1, 0, 18, 18, 0, 1),
        ("p1_toggle_from_0", 1, 0, 18, 18, 0, 0),
        ("p1_arg1_force", 1, 1, 18, 18, 0, 0),
    ]

    for cname, slot_idx, arg0, demon_id, target_slot, flag42, mode2c in cases:
        def run_variant(code_bytes, entry_addr):
            uc = create_emulator()
            uc.mem_write(entry_addr, code_bytes)
            calls_log = []
            install_stubs(uc, calls_log)

            uc.mem_write(0x0043dcf0, struct.pack('<I', CTX_ADDR))

            ctx_buf = bytearray(0x1000)
            struct.pack_into('<i', ctx_buf, 0x670, slot_idx)
            ctx_buf[0x42] = flag42
            struct.pack_into('<i', ctx_buf, 0x2c, mode2c)

            # setup widget pointers
            WIDGET_BASE = 0x10050000
            for i in range(4):
                struct.pack_into('<I', ctx_buf, 0x6c8 + i * 4, WIDGET_BASE + i * 0x30)
            for i in range(24):
                struct.pack_into('<I', ctx_buf, 0x6d8 + i * 4, WIDGET_BASE + 0x200 + i * 0x30)

            # stock slots ctx + 0x738 + i*8
            for i in range(24):
                val = target_slot if (i == target_slot) else 999
                struct.pack_into('<i', ctx_buf, 0x738 + i * 8, val)

            uc.mem_write(CTX_ADDR, bytes(ctx_buf))

            party_buf = bytearray(0x9200)
            if slot_idx > 0:
                party_buf[0x9107 + slot_idx] = demon_id & 0xFF
            uc.mem_write(PARTY_CTX_ADDR, bytes(party_buf))

            setup_call(uc, entry_addr, arg0)
            run_until_ret(uc)

            ret = uc.reg_read(UC_ARM_REG_R0)
            ctx_out = uc.mem_read(CTX_ADDR, 0x1000)
            return (ret, ctx_out, calls_log)

        orig_res = run_variant(load_original_bytes(0x002eff60, 512), 0x002eff60)
        comp_res = run_variant(staged_comp, 0x002eff60)

        assert orig_res[0] == comp_res[0], f"{cname}: ret mismatch (orig={orig_res[0]}, comp={comp_res[0]})"
        assert orig_res[1] == comp_res[1], f"{cname}: ctx mismatch"
        assert orig_res[2] == comp_res[2], f"{cname}: calls mismatch"

    print(f"PASS: camp_func_002eff60 (all {len(cases)} cases passed)")


if __name__ == "__main__":
    test_camp_func_002dad3c()
    test_camp_func_002e3684()
    test_func_002eb174()
    test_script_vm_func_002ece08()
    test_camp_func_002eff60()
    print("\nALL 5 CANDIDATES IN PART 17 PASSED DIFFERENTIAL VERIFICATION!")
