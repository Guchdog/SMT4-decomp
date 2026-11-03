#!/usr/bin/env python3
"""Differential test for batch 30 B part 4:
- func_00237f34 (0x00237F34, 104 B)
- func_0023a484 (0x0023A484, 96 B)
- func_0023a620 (0x0023A620, 112 B)
- camp_func_0023ec74 (0x0023EC74, 100 B)
- battle_func_00240744 (0x00240744, 100 B)
"""

from __future__ import annotations

from pathlib import Path
import struct
import sys

from unicorn import (
    Uc,
    UC_ARCH_ARM,
    UC_MODE_ARM,
    UC_HOOK_MEM_UNMAPPED,
    UC_HOOK_CODE,
)
from unicorn.arm_const import (
    UC_CPU_ARM_11MPCORE,
    UC_ARM_REG_C1_C0_2,
    UC_ARM_REG_FPEXC,
    UC_ARM_REG_R0,
    UC_ARM_REG_R1,
    UC_ARM_REG_R2,
    UC_ARM_REG_R3,
    UC_ARM_REG_R4,
    UC_ARM_REG_R5,
    UC_ARM_REG_R6,
    UC_ARM_REG_R7,
    UC_ARM_REG_R8,
    UC_ARM_REG_SB,
    UC_ARM_REG_SL,
    UC_ARM_REG_SP,
    UC_ARM_REG_LR,
    UC_ARM_REG_PC,
)

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k

ORIG_BIN = ROOT / "extracted/exefs/code.bin"
STACK_BASE = 0x10080000
STACK_SIZE = 0x10000
CODE_BASE = 0x00100000
CODE_SIZE = 0x00380000

COMPILED_FUNCTIONS = None
SOURCE = ROOT / "src/engine/leaf_batch30_b.cpp"

def load_original_bytes(addr: int, size: int) -> bytes:
    with open(ORIG_BIN, "rb") as f:
        f.seek(addr - CODE_BASE)
        return f.read(size)

def compile_function(func_name: str, out: Path, source: Path = SOURCE):
    global COMPILED_FUNCTIONS
    if COMPILED_FUNCTIONS is None:
        obj = out / "leaf_batch30_b.o"
        result = compile_tu_armv6k(source, obj, ROOT)
        if result.returncode != 0:
            raise RuntimeError(result.stderr)
        COMPILED_FUNCTIONS = extract_elf_functions_detailed(obj)
    if func_name not in COMPILED_FUNCTIONS:
        raise RuntimeError(f"{func_name} not in object")
    return COMPILED_FUNCTIONS[func_name]

def stage_body(body: bytes, relocs, target_addr: int, symbol_map: dict[str, int]) -> bytes:
    data = bytearray(body)
    for reloc in relocs:
        sym = reloc.symbol_name
        if sym not in symbol_map:
            raise RuntimeError(f"Unmapped relocation: {sym}")
        stub_addr = symbol_map[sym]
        rel_off = stub_addr - (target_addr + reloc.offset + 8)
        imm24 = (rel_off >> 2) & 0x00FFFFFF
        inst = struct.unpack_from("<I", data, reloc.offset)[0]
        inst = (inst & 0xFF000000) | imm24
        struct.pack_into("<I", data, reloc.offset, inst)
    return bytes(data)

def setup_uc() -> Uc:
    uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc.ctl_set_cpu_model(UC_CPU_ARM_11MPCORE)
    uc.reg_write(UC_ARM_REG_C1_C0_2, 0x00F00000)
    uc.reg_write(UC_ARM_REG_FPEXC, 0x40000000)

    uc.mem_map(CODE_BASE, CODE_SIZE)
    with open(ORIG_BIN, "rb") as f:
        code_data = f.read(CODE_SIZE)
    uc.mem_write(CODE_BASE, code_data)

    uc.mem_map(0x00480000, 0x00100000)
    uc.mem_map(STACK_BASE, STACK_SIZE)
    uc.mem_map(0x20000000, 0x00100000)

    def hook_unmapped(uc, access, address, size, value, user_data):
        page = address & ~0xFFF
        try:
            uc.mem_map(page, 0x1000)
        except Exception:
            pass
        return True

    uc.hook_add(UC_HOOK_MEM_UNMAPPED, hook_unmapped)
    return uc


def test_00237f34():
    print("--- Testing func_00237f34 ---")
    addr = 0x00237F34
    size = 104
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("func_00237f34", ROOT / "build")
    symbol_map = {"engine_func_00238990": 0x00238990}
    staged = stage_body(comp, relocs, addr, symbol_map)

    TABLE_BASE = 0x004171F8
    ELEMS_BASE = 0x004149C0
    ARG0 = 0x20005000

    def run_one(c_bytes, span_id, start_idx, count, helper_returns):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)

        # write span
        uc.mem_write(TABLE_BASE + span_id * 8, struct.pack("<II", start_idx, count))

        # write elems
        for i in range(start_idx, start_idx + count):
            uc.mem_write(ELEMS_BASE + i * 4, struct.pack("<HH", (i * 3) & 0xFFFF, (i * 7 + 1) & 0xFFFF))

        helper_calls = []
        def on_38990(uc, address, size, user_data):
            a0 = uc.reg_read(UC_ARM_REG_R0)
            p0 = uc.reg_read(UC_ARM_REG_R1)
            p1 = uc.reg_read(UC_ARM_REG_R2)
            assert a0 == ARG0
            call_num = len(helper_calls)
            helper_calls.append((p0, p1))
            ret = helper_returns[call_num] if call_num < len(helper_returns) else 1
            uc.reg_write(UC_ARM_REG_R0, ret)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        h_mock = uc.hook_add(UC_HOOK_CODE, on_38990, None, 0x00238990, 0x00238990)

        sp = STACK_BASE + STACK_SIZE - 0x1000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, 0x00200000)
        uc.reg_write(UC_ARM_REG_R0, ARG0)
        uc.reg_write(UC_ARM_REG_R1, span_id)

        def on_exit(uc, address, size, user_data):
            uc.emu_stop()

        h_exit = uc.hook_add(UC_HOOK_CODE, on_exit, None, 0x00200000, 0x00200000)
        uc.emu_start(addr, 0x00200000, timeout=1000000)
        uc.hook_del(h_exit)
        uc.hook_del(h_mock)

        r0 = uc.reg_read(UC_ARM_REG_R0)
        regs = [uc.reg_read(getattr(sys.modules[__name__], f"UC_ARM_REG_R{i}")) for i in range(4, 9)]
        return r0, helper_calls, regs

    cases = [
        (0, 10, 0, []),        # count == 0 -> returns 1
        (1, 5, 3, [1, 1, 1]),   # all succeed -> returns 1
        (2, 5, 3, [0, 1, 1]),   # first backward call fails -> returns 0
        (3, 5, 3, [1, 1, 0]),   # last backward call fails -> returns 0
    ]

    for span_id, start_idx, count, ret_list in cases:
        orig_r0, orig_calls, orig_regs = run_one(orig, span_id, start_idx, count, ret_list)
        comp_r0, comp_calls, comp_regs = run_one(staged, span_id, start_idx, count, ret_list)
        assert orig_r0 == comp_r0, f"Mismatch r0: orig={orig_r0}, comp={comp_r0}"
        assert orig_calls == comp_calls, f"Mismatch calls: orig={orig_calls}, comp={comp_calls}"
        assert orig_regs == comp_regs, f"Mismatch regs: orig={orig_regs}, comp={comp_regs}"

    print("func_00237f34: PASS")


def test_0023a484():
    print("--- Testing func_0023a484 ---")
    addr = 0x0023A484
    size = 96
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("func_0023a484", ROOT / "build")
    symbol_map = {
        "engine_func_00225dac": 0x00225DAC,
        "engine_func_003aff38": 0x003AFF38,
    }
    staged = stage_body(comp, relocs, addr, symbol_map)

    OBJ = 0x20001000
    TARGET = 0x20002000
    SUB = 0x20003000

    def run_one(c_bytes, has_target, has_sub, count, aff38_returns):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)

        FIELD_4_VAL = 0x123
        uc.mem_write(OBJ + 4, struct.pack("<I", FIELD_4_VAL))

        if has_target:
            uc.mem_write(TARGET + 0x10, struct.pack("<I", SUB if has_sub else 0))
            if has_sub:
                uc.mem_write(SUB + 0x48, struct.pack("<i", count))

        def on_225dac(uc, address, size, user_data):
            f4 = uc.reg_read(UC_ARM_REG_R0)
            assert f4 == FIELD_4_VAL
            uc.reg_write(UC_ARM_REG_R0, TARGET if has_target else 0)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        calls_3aff38 = []
        def on_3aff38(uc, address, size, user_data):
            sub = uc.reg_read(UC_ARM_REG_R0)
            assert sub == SUB
            idx = len(calls_3aff38)
            calls_3aff38.append(idx)
            ret = aff38_returns[idx] if idx < len(aff38_returns) else 1
            uc.reg_write(UC_ARM_REG_R0, ret)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        h1 = uc.hook_add(UC_HOOK_CODE, on_225dac, None, 0x00225DAC, 0x00225DAC)
        h2 = uc.hook_add(UC_HOOK_CODE, on_3aff38, None, 0x003AFF38, 0x003AFF38)

        sp = STACK_BASE + STACK_SIZE - 0x1000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, 0x00200000)
        uc.reg_write(UC_ARM_REG_R0, OBJ)

        def on_exit(uc, address, size, user_data):
            uc.emu_stop()

        h_exit = uc.hook_add(UC_HOOK_CODE, on_exit, None, 0x00200000, 0x00200000)
        uc.emu_start(addr, 0x00200000, timeout=1000000)
        uc.hook_del(h_exit)
        uc.hook_del(h1)
        uc.hook_del(h2)

        r0 = uc.reg_read(UC_ARM_REG_R0)
        regs = [uc.reg_read(getattr(sys.modules[__name__], f"UC_ARM_REG_R{i}")) for i in range(4, 7)]
        return r0, len(calls_3aff38), regs

    cases = [
        (False, False, 0, []),       # target == null -> 14
        (True, False, 0, []),        # sub == null -> 14
        (True, True, 0, []),         # count == 0 -> 0
        (True, True, -5, []),        # count < 0 -> 0
        (True, True, 3, [1, 1, 1]),  # all 1 -> returns 0
        (True, True, 3, [1, 0, 1]),  # returns 0 at i=1 -> returns 20
        (True, True, 3, [0, 1, 1]),  # returns 0 at i=0 -> returns 20
    ]

    for ht, hs, cnt, ret_list in cases:
        orig_r0, orig_nc, orig_regs = run_one(orig, ht, hs, cnt, ret_list)
        comp_r0, comp_nc, comp_regs = run_one(staged, ht, hs, cnt, ret_list)
        assert orig_r0 == comp_r0, f"Mismatch r0: orig={orig_r0}, comp={comp_r0}"
        assert orig_nc == comp_nc, f"Mismatch num calls: orig={orig_nc}, comp={comp_nc}"
        assert orig_regs == comp_regs, f"Mismatch regs: orig={orig_regs}, comp={comp_regs}"

    print("func_0023a484: PASS")


def test_0023a620():
    print("--- Testing func_0023a620 ---")
    addr = 0x0023A620
    size = 112
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("func_0023a620", ROOT / "build")
    symbol_map = {
        "engine_func_00225dac": 0x00225DAC,
        "engine_func_003eab5c": 0x003EAB5C,
    }
    staged = stage_body(comp, relocs, addr, symbol_map)

    OBJ = 0x20001000
    TARGET = 0x20002000
    SUB = 0x20003000
    RES = 0x20004000
    OUT_PTR = 0x20005000

    def run_one(c_bytes, is_null_obj, has_target, has_sub, sub_count, has_res, res_flag):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)

        uc.mem_write(OUT_PTR, struct.pack("<I", 0xDEADBEEF))

        if not is_null_obj:
            uc.mem_write(OBJ + 4, struct.pack("<I", 0x456))

        if has_target:
            uc.mem_write(TARGET + 0x10, struct.pack("<I", SUB if has_sub else 0))
            if has_sub:
                uc.mem_write(SUB + 0x48, struct.pack("<I", sub_count))

        if has_res:
            uc.mem_write(RES + 0x14, struct.pack("<B", res_flag))

        def on_225dac(uc, address, size, user_data):
            uc.reg_write(UC_ARM_REG_R0, TARGET if has_target else 0)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def on_3eab5c(uc, address, size, user_data):
            uc.reg_write(UC_ARM_REG_R0, RES if has_res else 0)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        h1 = uc.hook_add(UC_HOOK_CODE, on_225dac, None, 0x00225DAC, 0x00225DAC)
        h2 = uc.hook_add(UC_HOOK_CODE, on_3eab5c, None, 0x003EAB5C, 0x003EAB5C)

        sp = STACK_BASE + STACK_SIZE - 0x1000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, 0x00200000)
        uc.reg_write(UC_ARM_REG_R0, 0 if is_null_obj else OBJ)
        uc.reg_write(UC_ARM_REG_R1, 0x777)
        uc.reg_write(UC_ARM_REG_R2, OUT_PTR)

        def on_exit(uc, address, size, user_data):
            uc.emu_stop()

        h_exit = uc.hook_add(UC_HOOK_CODE, on_exit, None, 0x00200000, 0x00200000)
        uc.emu_start(addr, 0x00200000, timeout=1000000)
        uc.hook_del(h_exit)
        uc.hook_del(h1)
        uc.hook_del(h2)

        r0 = uc.reg_read(UC_ARM_REG_R0)
        out_val = struct.unpack("<I", uc.mem_read(OUT_PTR, 4))[0]
        regs = [uc.reg_read(getattr(sys.modules[__name__], f"UC_ARM_REG_R{i}")) for i in range(4, 7)]
        return r0, out_val, regs

    cases = [
        (True, False, False, 0, False, 0),        # obj == null -> r0=1, out=0
        (False, True, False, 0, False, 0),       # sub == null -> r0=14, out=0
        (False, True, True, 0, False, 0),        # sub_count == 0 -> r0=14, out=0
        (False, True, True, 42, False, 0),       # res == null -> r0=14, out=0
        (False, True, True, 42, True, 1),        # res[0x14] == 1 -> r0=14, out=0
        (False, True, True, 42, True, 0),        # res[0x14] == 0 -> r0=0, out=42!
        (False, True, True, 1000, True, 0),      # res[0x14] == 0 -> r0=0, out=1000!
    ]

    for is_null, ht, hs, cnt, hr, rf in cases:
        orig_r0, orig_out, orig_regs = run_one(orig, is_null, ht, hs, cnt, hr, rf)
        comp_r0, comp_out, comp_regs = run_one(staged, is_null, ht, hs, cnt, hr, rf)
        assert orig_r0 == comp_r0, f"Mismatch r0: orig={orig_r0}, comp={comp_r0}"
        assert orig_out == comp_out, f"Mismatch out: orig={orig_out}, comp={comp_out}"
        assert orig_regs == comp_regs, f"Mismatch regs: orig={orig_regs}, comp={comp_regs}"

    print("func_0023a620: PASS")


def test_0023ec74():
    print("--- Testing camp_func_0023ec74 ---")
    addr = 0x0023EC74
    size = 100
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("camp_func_0023ec74", ROOT / "build")
    symbol_map = {
        "camp_func_002c0ec4": 0x002C0EC4,
        "camp_func_002c0e9c": 0x002C0E9C,
        "camp_func_002c0e4c": 0x002C0E4C,
        "engine_func_0022add0": 0x0022ADD0,
    }
    staged = stage_body(comp, relocs, addr, symbol_map)

    RES1 = 0x20001000
    BASE = 0x20002000
    OBJ = 0x20003000
    ITEM = 0x20004000

    def run_one(c_bytes, idx, max_count, item_ret):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)

        # [0x00433158] = OBJ
        uc.mem_write(0x00433158, struct.pack("<I", OBJ))

        def on_2c0ec4(uc, address, size, user_data):
            assert uc.reg_read(UC_ARM_REG_R0) == 2
            assert uc.reg_read(UC_ARM_REG_R1) == 2
            uc.reg_write(UC_ARM_REG_R0, RES1)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def on_2c0e9c(uc, address, size, user_data):
            uc.reg_write(UC_ARM_REG_R0, BASE)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def on_2c0e4c(uc, address, size, user_data):
            assert uc.reg_read(UC_ARM_REG_R0) == RES1
            uc.reg_write(UC_ARM_REG_R0, max_count)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def on_22add0(uc, address, size, user_data):
            assert uc.reg_read(UC_ARM_REG_R0) == OBJ
            assert uc.reg_read(UC_ARM_REG_R1) == (idx & 0xFFFFFFFF)
            uc.reg_write(UC_ARM_REG_R0, item_ret)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        h1 = uc.hook_add(UC_HOOK_CODE, on_2c0ec4, None, 0x002C0EC4, 0x002C0EC4)
        h2 = uc.hook_add(UC_HOOK_CODE, on_2c0e9c, None, 0x002C0E9C, 0x002C0E9C)
        h3 = uc.hook_add(UC_HOOK_CODE, on_2c0e4c, None, 0x002C0E4C, 0x002C0E4C)
        h4 = uc.hook_add(UC_HOOK_CODE, on_22add0, None, 0x0022ADD0, 0x0022ADD0)

        sp = STACK_BASE + STACK_SIZE - 0x1000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, 0x00200000)
        uc.reg_write(UC_ARM_REG_R0, idx & 0xFFFFFFFF)

        def on_exit(uc, address, size, user_data):
            uc.emu_stop()

        h_exit = uc.hook_add(UC_HOOK_CODE, on_exit, None, 0x00200000, 0x00200000)
        uc.emu_start(addr, 0x00200000, timeout=1000000)
        uc.hook_del(h_exit)
        uc.hook_del(h1)
        uc.hook_del(h2)
        uc.hook_del(h3)
        uc.hook_del(h4)

        r0 = uc.reg_read(UC_ARM_REG_R0)
        regs = [uc.reg_read(getattr(sys.modules[__name__], f"UC_ARM_REG_R{i}")) for i in range(4, 7)]
        return r0, regs

    cases = [
        (-1, 10, 0),         # idx < 0 -> returns BASE
        (-5, 10, 0),         # idx < 0 -> returns BASE
        (10, 10, 0),         # idx >= max_count -> returns BASE
        (12, 10, 0),         # idx >= max_count -> returns BASE
        (0, 10, 0),          # idx == 0, null item -> returns BASE + 0*28 = BASE
        (2, 10, 0),          # idx == 2, null item -> returns BASE + 2*28
        (5, 10, 0),          # idx == 5, null item -> returns BASE + 5*28
        (2, 10, ITEM),       # idx == 2, non-null item -> returns ITEM
    ]

    for idx, mc, itm in cases:
        orig_r0, orig_regs = run_one(orig, idx, mc, itm)
        comp_r0, comp_regs = run_one(staged, idx, mc, itm)
        assert orig_r0 == comp_r0, f"Mismatch r0: idx={idx}, mc={mc}, itm={itm} -> orig={hex(orig_r0)}, comp={hex(comp_r0)}"
        assert orig_regs == comp_regs, f"Mismatch regs: orig={orig_regs}, comp={comp_regs}"

    print("camp_func_0023ec74: PASS")


def test_00240744():
    print("--- Testing battle_func_00240744 ---")
    addr = 0x00240744
    size = 100
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("battle_func_00240744", ROOT / "build")
    symbol_map = {
        "battle_func_0024a80c": 0x0024A80C,
        "battle_func_00249fac": 0x00249FAC,
    }
    staged = stage_body(comp, relocs, addr, symbol_map)

    OBJ = 0x20001000
    TAGS_BASE = 0x20008000

    def run_one(c_bytes, tag_strings):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)

        # Clear obj slots
        uc.mem_write(OBJ + 0x25C0, b"\x00" * (11 * 140))

        # Setup 11 slots
        for i in range(11):
            slot = OBJ + 0x25C0 + i * 140
            tag_str = tag_strings[i]
            if tag_str is not None:
                tag_addr = TAGS_BASE + i * 0x100
                uc.mem_write(tag_addr, tag_str.encode("ascii") + b"\x00")
                uc.mem_write(slot + 4, struct.pack("<I", tag_addr))

        calls = []

        def on_24a80c(uc, address, size, user_data):
            slot_p8 = uc.reg_read(UC_ARM_REG_R0)
            slot = slot_p8 - 8
            idx = (slot - (OBJ + 0x25C0)) // 140
            calls.append(("24a80c", idx))
            uc.reg_write(UC_ARM_REG_R0, (idx * 5 + 3) & 0xFF)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def on_249fac(uc, address, size, user_data):
            code = uc.reg_read(UC_ARM_REG_R0)
            tag = uc.reg_read(UC_ARM_REG_R1)
            calls.append(("249fac", code))
            uc.reg_write(UC_ARM_REG_R0, (code ^ 0x5A) & 0xFF)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        h1 = uc.hook_add(UC_HOOK_CODE, on_24a80c, None, 0x0024A80C, 0x0024A80C)
        h2 = uc.hook_add(UC_HOOK_CODE, on_249fac, None, 0x00249FAC, 0x00249FAC)

        sp = STACK_BASE + STACK_SIZE - 0x1000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, 0x00200000)
        uc.reg_write(UC_ARM_REG_R0, OBJ)

        def on_exit(uc, address, size, user_data):
            uc.emu_stop()

        h_exit = uc.hook_add(UC_HOOK_CODE, on_exit, None, 0x00200000, 0x00200000)
        uc.emu_start(addr, 0x00200000, timeout=1000000)
        uc.hook_del(h_exit)
        uc.hook_del(h1)
        uc.hook_del(h2)

        # Read slot[0] for each of the 11 slots
        slot_bytes = [uc.mem_read(OBJ + 0x25C0 + i * 140, 1)[0] for i in range(11)]
        regs = [uc.reg_read(getattr(sys.modules[__name__], f"UC_ARM_REG_R{i}")) for i in range(4, 9)]
        return slot_bytes, calls, regs

    scenarios = [
        ["VER" + str(i) for i in range(11)], # all VER
        ["ATK" for _ in range(11)],           # no VER
        ["VER" if i in (0, 5, 10) else "DEF" for i in range(11)], # sparse
    ]

    for tags in scenarios:
        orig_bytes, orig_calls, orig_regs = run_one(orig, tags)
        comp_bytes, comp_calls, comp_regs = run_one(staged, tags)
        assert orig_bytes == comp_bytes, f"Mismatch bytes: orig={orig_bytes}, comp={comp_bytes}"
        assert orig_calls == comp_calls, f"Mismatch calls: orig={orig_calls}, comp={comp_calls}"
        assert orig_regs == comp_regs, f"Mismatch regs: orig={orig_regs}, comp={comp_regs}"

    print("battle_func_00240744: PASS")


if __name__ == "__main__":
    test_00237f34()
    test_0023a484()
    test_0023a620()
    test_0023ec74()
    test_00240744()
    print("\nALL 5 FUNCTIONS PASSED 100% DIFFERENTIAL VERIFICATION!")
