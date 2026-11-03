#!/usr/bin/env python3
"""Differential test for batch 30 B part 12:
- camp_func_00293c2c (0x00293C2C, 108 B)
- ui_func_002940ac (0x002940AC, 112 B)
- script_vm_func_00296154 (0x00296154, 120 B)
- camp_func_00298a74 (0x00298A74, 112 B)
- engine_func_00299874 (0x00299874, 100 B)
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
    UC_ARM_REG_S0,
    UC_ARM_REG_S1,
    UC_ARM_REG_S2,
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


def test_00293c2c():
    print("--- Testing camp_func_00293c2c ---")
    addr = 0x00293C2C
    size = 108
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("camp_func_00293c2c", ROOT / "build")

    STUB_SLOT = 0x0026F25C
    staged = stage_body(comp, relocs, addr, {
        "camp_func_0026f25c": STUB_SLOT,
    })

    OBJ = 0x20001000
    SLOT_BASE = 0x20010000
    stub_code = struct.pack("<I", 0xE12FFF1E) # bx lr

    def run_one(c_bytes, flags, type_val, hp_list):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)
        uc.mem_write(STUB_SLOT, stub_code)

        # Map memory for large OBJ (needs up to 0x5000)
        uc.mem_write(OBJ, b"\x00" * 0x5000)
        uc.mem_write(OBJ + 0x44A8, struct.pack("<I", flags))
        uc.mem_write(OBJ + 0x2F34, struct.pack("<I", type_val))

        for i, hp in enumerate(hp_list):
            slot_addr = SLOT_BASE + i * 0x60
            uc.mem_write(slot_addr, b"\x00" * 0x60)
            uc.mem_write(slot_addr + 0x48, struct.pack("<H", hp))

        def code_hook(uc, address, sz, user_data):
            if address == STUB_SLOT:
                idx = uc.reg_read(UC_ARM_REG_R0)
                uc.reg_write(UC_ARM_REG_R0, SLOT_BASE + idx * 0x60)

        h = uc.hook_add(UC_HOOK_CODE, code_hook)

        sp = STACK_BASE + STACK_SIZE - 0x1000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_R0, OBJ)
        uc.reg_write(UC_ARM_REG_LR, 0)
        uc.reg_write(UC_ARM_REG_PC, addr)

        uc.emu_start(addr, 0, count=500)

        ret = uc.reg_read(UC_ARM_REG_R0)
        return ret

    test_cases = [
        # (flags, type_val, hp_list)
        (0x40, 5, [0]*12),           # flag 0x40 -> 1
        (0, 1, [0]*12),              # type 1..4 -> 1
        (0, 4, [0]*12),              # type 1..4 -> 1
        (0, 5, [0]*12),              # type 5, all dead -> 0
        (0, 5, [100] + [0]*11),      # type 5, 1 alive -> 1
        (0, 5, [0]*5 + [50] + [0]*6),# type 5, 1 alive -> 1
    ]

    for fl, tp, hps in test_cases:
        r1 = run_one(orig, fl, tp, hps)
        r2 = run_one(staged, fl, tp, hps)
        assert r1 == r2, f"Ret mismatch: orig={r1}, comp={r2} for flags={hex(fl)}, type={tp}"
    print("camp_func_00293c2c: PASS")


def test_002940ac():
    print("--- Testing ui_func_002940ac ---")
    addr = 0x002940AC
    size = 112
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("ui_func_002940ac", ROOT / "build")

    STUB_SET_POS = 0x0025C0F0
    staged = stage_body(comp, relocs, addr, {
        "engine_func_0025c0f0": STUB_SET_POS,
    })

    OBJ = 0x20001000
    HEAD_PTR = 0x20002000
    HEAD_NODE = 0x20003000
    SUB_PTRS = [0x20004000, 0x20005000, 0x20006000]
    SUB_NODES = [0x20007000, 0x20008000, 0x20009000]
    stub_code = struct.pack("<I", 0xE12FFF1E) # bx lr

    def run_one(c_bytes, x, y, z, active_subs):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)
        uc.mem_write(STUB_SET_POS, stub_code)

        uc.mem_write(OBJ, b"\x00" * 0x200)
        uc.mem_write(HEAD_PTR, b"\x00" * 0x20)
        uc.mem_write(HEAD_PTR + 8, struct.pack("<I", HEAD_NODE))
        uc.mem_write(OBJ + 8, struct.pack("<I", HEAD_PTR))

        for i in range(3):
            slot_addr = OBJ + i * 80
            if active_subs[i]:
                uc.mem_write(SUB_PTRS[i], b"\x00" * 0x20)
                uc.mem_write(SUB_PTRS[i] + 8, struct.pack("<I", SUB_NODES[i]))
                uc.mem_write(slot_addr + 0x18, struct.pack("<I", SUB_PTRS[i]))
            else:
                uc.mem_write(slot_addr + 0x18, struct.pack("<I", 0))

        pos_calls = []

        def code_hook(uc, address, sz, user_data):
            if address == STUB_SET_POS:
                node = uc.reg_read(UC_ARM_REG_R0)
                p1 = uc.reg_read(UC_ARM_REG_R1)
                s0_raw = uc.reg_read(UC_ARM_REG_S0)
                s1_raw = uc.reg_read(UC_ARM_REG_S1)
                s2_raw = uc.reg_read(UC_ARM_REG_S2)
                xf = struct.unpack("<f", struct.pack("<I", s0_raw))[0]
                yf = struct.unpack("<f", struct.pack("<I", s1_raw))[0]
                zf = struct.unpack("<f", struct.pack("<I", s2_raw))[0]
                pos_calls.append((node, p1, round(xf, 2), round(yf, 2), round(zf, 2)))

        h = uc.hook_add(UC_HOOK_CODE, code_hook)

        sp = STACK_BASE + STACK_SIZE - 0x1000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_R0, OBJ)
        uc.reg_write(UC_ARM_REG_S0, struct.unpack("<I", struct.pack("<f", x))[0])
        uc.reg_write(UC_ARM_REG_S1, struct.unpack("<I", struct.pack("<f", y))[0])
        uc.reg_write(UC_ARM_REG_S2, struct.unpack("<I", struct.pack("<f", z))[0])
        uc.reg_write(UC_ARM_REG_LR, 0)
        uc.reg_write(UC_ARM_REG_PC, addr)

        uc.emu_start(addr, 0, count=500)

        return pos_calls

    test_cases = [
        (1.5, 2.5, 3.5, [True, True, True]),
        (10.0, -5.0, 0.0, [False, True, False]),
        (0.0, 0.0, 0.0, [False, False, False]),
    ]

    for x, y, z, subs in test_cases:
        c1 = run_one(orig, x, y, z, subs)
        c2 = run_one(staged, x, y, z, subs)
        assert c1 == c2, f"Pos calls mismatch: orig={c1}, comp={c2}"
    print("ui_func_002940ac: PASS")


def test_00296154():
    print("--- Testing script_vm_func_00296154 ---")
    addr = 0x00296154
    size = 120
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("script_vm_func_00296154", ROOT / "build")

    STUB_NODE = 0x002BF6D0
    staged = stage_body(comp, relocs, addr, {
        "camp_func_002bf6d0": STUB_NODE,
    })

    DST = 0x20001000
    NODE = 0x20002000
    PARENT = 0x20003000
    stub_code = struct.pack("<I", 0xE12FFF1E) # bx lr

    def run_one(c_bytes, has_p, dx, dy, w, h, x0, y0):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)
        uc.mem_write(STUB_NODE, stub_code)

        uc.mem_write(DST, b"\x00" * 0x30)
        uc.mem_write(NODE, b"\x00" * 0x30)
        struct.pack_into("<HHHH", uc.mem_read(NODE, 0x10), 4, w, h, x0, y0)
        uc.mem_write(NODE + 4, struct.pack("<HHHH", w, h, x0, y0))

        if has_p:
            uc.mem_write(PARENT, struct.pack("<hh", dx, dy))
            uc.mem_write(NODE + 0xC, struct.pack("<I", PARENT))
        else:
            uc.mem_write(NODE + 0xC, struct.pack("<I", 0))

        def code_hook(uc, address, sz, user_data):
            if address == STUB_NODE:
                uc.reg_write(UC_ARM_REG_R0, NODE)

        h = uc.hook_add(UC_HOOK_CODE, code_hook)

        sp = STACK_BASE + STACK_SIZE - 0x1000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_R0, DST)
        uc.reg_write(UC_ARM_REG_R1, 10)
        uc.reg_write(UC_ARM_REG_R2, 20)
        uc.reg_write(UC_ARM_REG_LR, 0)
        uc.reg_write(UC_ARM_REG_PC, addr)

        uc.emu_start(addr, 0, count=200)

        out_x, out_y = struct.unpack_from("<HH", uc.mem_read(DST + 0x18, 4))
        return out_x, out_y

    test_cases = [
        # (has_p, dx, dy, w, h, x0, y0)
        (True, 10, -20, 100, 200, 50, 60),
        (True, -5, -7, 100, 200, 50, 60),
        (False, 0, 0, 80, 40, 10, 20),
        (False, 0, 0, 0x8050, 0x8030, 10, 20), # high bit set
    ]

    for tc in test_cases:
        x1, y1 = run_one(orig, *tc)
        x2, y2 = run_one(staged, *tc)
        assert (x1, y1) == (x2, y2), f"Result mismatch: orig=({x1}, {y1}), comp=({x2}, {y2}) for {tc}"
    print("script_vm_func_00296154: PASS")


def test_00298a74():
    print("--- Testing camp_func_00298a74 ---")
    addr = 0x00298A74
    size = 112
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("camp_func_00298a74", ROOT / "build")

    STUB_NOTIF = 0x002AE3F0
    STUB_B66 = 0x002B66EC
    STUB_AC7 = 0x0029AC70
    STUB_89E = 0x002A89E4
    STUB_ABC = 0x0029ABC0

    staged = stage_body(comp, relocs, addr, {
        "battle_func_002ae3f0": STUB_NOTIF,
        "script_vm_func_002b66ec": STUB_B66,
        "battle_func_0029ac70": STUB_AC7,
        "camp_func_002a89e4": STUB_89E,
        "battle_func_0029abc0": STUB_ABC,
    })

    PTR1 = 0x20001000
    PTR2 = 0x20002000
    stub_code = struct.pack("<I", 0xE12FFF1E) # bx lr

    def run_one(c_bytes, arg0, arg1, current_val, limit_val):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)
        uc.mem_write(STUB_NOTIF, stub_code)
        uc.mem_write(STUB_B66, stub_code)
        uc.mem_write(STUB_AC7, stub_code)
        uc.mem_write(STUB_89E, stub_code)
        uc.mem_write(STUB_ABC, stub_code)

        target_ptr = PTR1 if arg0 < 0 else PTR2
        uc.mem_write(target_ptr, b"\x00" * 0x40)
        uc.mem_write(target_ptr + 0x2C, struct.pack("<h", current_val))

        notif_calls = []

        def code_hook(uc, address, sz, user_data):
            if address == STUB_NOTIF:
                notif_calls.append(uc.reg_read(UC_ARM_REG_R0))
            elif address == STUB_B66:
                uc.reg_write(UC_ARM_REG_R0, PTR1)
            elif address == STUB_AC7:
                uc.reg_write(UC_ARM_REG_R0, limit_val)
            elif address == STUB_89E:
                uc.reg_write(UC_ARM_REG_R0, PTR2)
            elif address == STUB_ABC:
                uc.reg_write(UC_ARM_REG_R0, limit_val)

        h = uc.hook_add(UC_HOOK_CODE, code_hook)

        sp = STACK_BASE + STACK_SIZE - 0x1000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_R0, arg0)
        uc.reg_write(UC_ARM_REG_R1, arg1)
        uc.reg_write(UC_ARM_REG_LR, 0)
        uc.reg_write(UC_ARM_REG_PC, addr)

        uc.emu_start(addr, 0, count=200)

        ret = uc.reg_read(UC_ARM_REG_R0)
        return ret, notif_calls

    test_cases = [
        # (arg0, arg1, current, limit)
        (-1, 5, 10, 5),     # limit <= current -> 1
        (-1, 5, 5, 10),     # limit > current -> 0
        (2, 5, 10, 5),      # current >= limit -> 1
        (2, 5, 5, 10),      # current < limit -> 0
    ]

    for a0, a1, cur, lim in test_cases:
        r1, n1 = run_one(orig, a0, a1, cur, lim)
        r2, n2 = run_one(staged, a0, a1, cur, lim)
        assert r1 == r2, f"Ret mismatch: orig={r1}, comp={r2} for a0={a0}, cur={cur}, lim={lim}"
        assert n1 == n2, f"Notif mismatch: orig={n1}, comp={n2}"
    print("camp_func_00298a74: PASS")


def test_00299874():
    print("--- Testing engine_func_00299874 ---")
    addr = 0x00299874
    size = 100
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("engine_func_00299874", ROOT / "build")

    STUB_STATE = 0x00247344
    STUB_OBJ = 0x002B47CC
    staged = stage_body(comp, relocs, addr, {
        "script_vm_func_00247344": STUB_STATE,
        "engine_func_002b47cc": STUB_OBJ,
    })

    OBJ = 0x20001000
    stub_code = struct.pack("<I", 0xE12FFF1E) # bx lr

    def run_one(c_bytes, has_obj, flags, state):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)
        uc.mem_write(STUB_STATE, stub_code)
        uc.mem_write(STUB_OBJ, stub_code)

        if has_obj:
            uc.mem_write(OBJ, b"\x00" * 0x80)
            uc.mem_write(OBJ + 0x60, struct.pack("<B", flags))

        def code_hook(uc, address, sz, user_data):
            if address == STUB_STATE:
                uc.reg_write(UC_ARM_REG_R0, state)
            elif address == STUB_OBJ:
                uc.reg_write(UC_ARM_REG_R0, OBJ if has_obj else 0)

        h = uc.hook_add(UC_HOOK_CODE, code_hook)

        sp = STACK_BASE + STACK_SIZE - 0x1000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_R0, 123)
        uc.reg_write(UC_ARM_REG_LR, 0)
        uc.reg_write(UC_ARM_REG_PC, addr)

        uc.emu_start(addr, 0, count=200)

        ret = uc.reg_read(UC_ARM_REG_R0)
        return ret

    test_cases = [
        # (has_obj, flags, state)
        (False, 0, 4),      # no obj -> 0
        (True, 1, 4),       # flags & 1, state 4 -> 1
        (True, 4, 5),       # flags & 4, state 5 -> 1
        (True, 2, 1),       # flags & 2, state 1 -> 1
        (True, 1, 5),       # mismatch -> 0
        (True, 0, 4),       # flags 0 -> 0
    ]

    for tc in test_cases:
        r1 = run_one(orig, *tc)
        r2 = run_one(staged, *tc)
        assert r1 == r2, f"Ret mismatch: orig={r1}, comp={r2} for {tc}"
    print("engine_func_00299874: PASS")


def main():
    test_00293c2c()
    test_002940ac()
    test_00296154()
    test_00298a74()
    test_00299874()
    print("\nALL 5 FUNCTIONS IN BATCH 30 B PART 12 PASSED WITH 100% DIFFERENTIAL FIDELITY!")

if __name__ == "__main__":
    main()
