#!/usr/bin/env python3
"""Differential test for batch 30 B part 2:
- func_00226d54 (0x00226D54, 96 B)
- ui_func_00227c48 (0x00227C48, 96 B)
- ui_func_00228338 (0x00228338, 124 B)
- script_vm_func_00229a34 (0x00229A34, 116 B)
- script_vm_func_0022a2b0 (0x0022A2B0, 116 B)
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


def test_00226d54():
    print("--- Testing func_00226d54 ---")
    addr = 0x00226D54
    size = 96
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("func_00226d54", ROOT / "build")
    staged = stage_body(comp, relocs, addr, {})

    def run_one(c_bytes, state, f8, node1_val, node2_val):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)

        PTR = 0x20001000
        NODE1 = 0x20002000
        NODE2 = 0x20003000

        # Setup struct at PTR
        # ptr + 0x2C: state
        # ptr + 8: f8
        uc.mem_write(PTR + 0x2C, struct.pack("<I", state))
        uc.mem_write(PTR + 8, struct.pack("<I", f8))

        idx = 1 if state == 4 else (2 if state == 5 else 0)

        # clear pointer slots
        for i in range(3):
            uc.mem_write(PTR + 0x0C + i * 4, struct.pack("<I", 0))
            uc.mem_write(PTR + 0x18 + i * 4, struct.pack("<I", 0))

        if node1_val is not None:
            uc.mem_write(PTR + 0x0C + idx * 4, struct.pack("<I", NODE1))
            uc.mem_write(NODE1 + 0x38, struct.pack("<f", node1_val))

        if node2_val is not None:
            uc.mem_write(PTR + 0x18 + idx * 4, struct.pack("<I", NODE2))
            uc.mem_write(NODE2 + 0x38, struct.pack("<f", node2_val))

        sp = STACK_BASE + STACK_SIZE - 0x1000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, 0x00200000)
        uc.reg_write(UC_ARM_REG_R0, PTR)
        uc.reg_write(UC_ARM_REG_S0, 0)
        uc.reg_write(UC_ARM_REG_S1, 0)

        # Hook return address
        def on_exit(uc, address, size, user_data):
            uc.emu_stop()

        h_exit = uc.hook_add(UC_HOOK_CODE, on_exit, None, 0x00200000, 0x00200000)
        uc.emu_start(addr, 0x00200000, timeout=1000000)
        uc.hook_del(h_exit)

        # read s0 float
        s0_raw = uc.reg_read(UC_ARM_REG_S0)
        # convert integer bits to float
        s0_float = struct.unpack("<f", struct.pack("<I", s0_raw))[0]
        return s0_float

    cases = [
        # (state, f8, node1_val, node2_val)
        (0, 0, 1.0, 2.0),
        (4, 0, 5.0, 10.0),
        (0, 1, 3.5, 1.2),
        (0, 1, 1.2, 3.5),
        (4, 1, 7.5, 2.0),
        (4, 1, 2.0, 8.5),
        (5, 1, 10.0, 12.5),
        (5, 1, 15.0, 3.0),
        (4, 1, None, 4.0),
        (4, 1, 4.0, None),
        (4, 1, None, None),
        (4, 1, -2.0, -5.0),
    ]

    for state, f8, n1, n2 in cases:
        orig_s0 = run_one(orig, state, f8, n1, n2)
        comp_s0 = run_one(staged, state, f8, n1, n2)
        assert abs(orig_s0 - comp_s0) < 1e-5, f"Mismatch: state={state}, f8={f8}, n1={n1}, n2={n2} -> orig={orig_s0}, comp={comp_s0}"

    print("func_00226d54: PASS")


def test_00227c48():
    print("--- Testing ui_func_00227c48 ---")
    addr = 0x00227C48
    size = 96
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("ui_func_00227c48", ROOT / "build")
    symbol_map = {"ui_func_00282b94": 0x00282B94}
    staged = stage_body(comp, relocs, addr, symbol_map)

    ITEM_BASE = 0x20005000

    def run_one(c_bytes, mock_pattern):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)

        CONTAINER = 0x20001000
        INNER_PTR = 0x20001080
        DST = 0x20002000

        uc.mem_write(CONTAINER, struct.pack("<I", INNER_PTR))
        # Zero out dst area
        uc.mem_write(DST + 0x900, b"\xaa" * (109 * 10 + 0x100))

        # Hook ui_func_00282b94
        def on_282b94(uc, address, size, user_data):
            inner = uc.reg_read(UC_ARM_REG_R0)
            idx = uc.reg_read(UC_ARM_REG_R1)
            assert inner == INNER_PTR
            if mock_pattern(idx):
                item = ITEM_BASE + idx * 0x200
                uc.mem_write(item + 0x1B4, struct.pack("<HH", (idx * 3) & 0xFFFF, (idx * 7 + 1) & 0xFFFF))
                uc.reg_write(UC_ARM_REG_R0, item)
            else:
                uc.reg_write(UC_ARM_REG_R0, 0)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        h_mock = uc.hook_add(UC_HOOK_CODE, on_282b94, None, 0x00282B94, 0x00282B94)

        sp = STACK_BASE + STACK_SIZE - 0x1000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, 0x00200000)
        uc.reg_write(UC_ARM_REG_R0, CONTAINER)
        uc.reg_write(UC_ARM_REG_R1, DST)

        def on_exit(uc, address, size, user_data):
            uc.emu_stop()

        h_exit = uc.hook_add(UC_HOOK_CODE, on_exit, None, 0x00200000, 0x00200000)
        uc.emu_start(addr, 0x00200000, timeout=2000000)
        uc.hook_del(h_exit)
        uc.hook_del(h_mock)

        # Read DST memory
        dst_mem = uc.mem_read(DST + 0x900, 109 * 10 + 0x100)
        regs = [uc.reg_read(getattr(sys.modules[__name__], f"UC_ARM_REG_R{i}")) for i in range(4, 9)]
        return dst_mem, regs

    patterns = [
        lambda idx: True,
        lambda idx: False,
        lambda idx: idx % 2 == 0,
        lambda idx: idx in (0, 50, 108),
    ]

    for p in patterns:
        orig_mem, orig_regs = run_one(orig, p)
        comp_mem, comp_regs = run_one(staged, p)
        assert orig_mem == comp_mem, "Memory mismatch in ui_func_00227c48"
        assert orig_regs == comp_regs, f"Register mismatch: orig={orig_regs}, comp={comp_regs}"

    print("ui_func_00227c48: PASS")


def test_00228338():
    print("--- Testing ui_func_00228338 ---")
    addr = 0x00228338
    size = 124
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("ui_func_00228338", ROOT / "build")
    symbol_map = {
        "func_00293c98": 0x00293C98,
        "battle_func_002934d4": 0x002934D4,
        "engine_func_002aa7f4": 0x002AA7F4,
    }
    staged = stage_body(comp, relocs, addr, symbol_map)

    UI_CTX = 0x20004000
    BASE = 0x20005000

    def run_one(c_bytes, battle_ret, match_idx):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)

        CTX = 0x20001000
        uc.mem_write(CTX + 0x1CFC, struct.pack("<I", BASE))

        # Setup 4 slots at BASE + 0x58 + i * 22
        for i in range(4):
            slot = BASE + 0x58 + i * 22
            val = (i * 100 - 50) & 0xFFFF
            uc.mem_write(slot + 0x10, struct.pack("<h", struct.unpack("<h", struct.pack("<H", val))[0]))

        def on_ctx(uc, address, size, user_data):
            uc.reg_write(UC_ARM_REG_R0, UI_CTX)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def on_battle(uc, address, size, user_data):
            assert uc.reg_read(UC_ARM_REG_R0) == UI_CTX
            uc.reg_write(UC_ARM_REG_R0, battle_ret)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def on_aa7f4(uc, address, size, user_data):
            a0 = uc.reg_read(UC_ARM_REG_R0)
            a1 = uc.reg_read(UC_ARM_REG_R1)
            assert a0 == 0x00400958
            # calculate which slot
            slot_idx = (a1 - (BASE + 0x58)) // 22
            ret = 0 if slot_idx == match_idx else 1
            uc.reg_write(UC_ARM_REG_R0, ret)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        h_ctx = uc.hook_add(UC_HOOK_CODE, on_ctx, None, 0x00293C98, 0x00293C98)
        h_bat = uc.hook_add(UC_HOOK_CODE, on_battle, None, 0x002934D4, 0x002934D4)
        h_aa = uc.hook_add(UC_HOOK_CODE, on_aa7f4, None, 0x002AA7F4, 0x002AA7F4)

        sp = STACK_BASE + STACK_SIZE - 0x1000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, 0x00200000)
        uc.reg_write(UC_ARM_REG_R0, CTX)

        def on_exit(uc, address, size, user_data):
            uc.emu_stop()

        h_exit = uc.hook_add(UC_HOOK_CODE, on_exit, None, 0x00200000, 0x00200000)
        uc.emu_start(addr, 0x00200000, timeout=1000000)
        uc.hook_del(h_exit)
        uc.hook_del(h_ctx)
        uc.hook_del(h_bat)
        uc.hook_del(h_aa)

        r0 = uc.reg_read(UC_ARM_REG_R0)
        # convert to signed 32-bit
        if r0 >= 0x80000000:
            r0 -= 0x100000000
        return r0

    cases = [
        (1, -1),   # battle_func returns != 0 -> returns -1
        (0, 0),    # match at slot 0
        (0, 1),    # match at slot 1
        (0, 2),    # match at slot 2
        (0, 3),    # match at slot 3
        (0, -1),   # no match -> returns 30
    ]

    for b_ret, m_idx in cases:
        orig_r0 = run_one(orig, b_ret, m_idx)
        comp_r0 = run_one(staged, b_ret, m_idx)
        assert orig_r0 == comp_r0, f"Mismatch: battle_ret={b_ret}, match_idx={m_idx} -> orig={orig_r0}, comp={comp_r0}"

    print("ui_func_00228338: PASS")


def test_00229a34():
    print("--- Testing script_vm_func_00229a34 ---")
    addr = 0x00229A34
    size = 116
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("script_vm_func_00229a34", ROOT / "build")
    symbol_map = {"script_vm_func_002b6e44": 0x002B6E44}
    staged = stage_body(comp, relocs, addr, symbol_map)

    P_MGR_PTR = 0x20001000
    NODE_BASE = 0x20002000

    def run_one(c_bytes, nodes, b6e44_results):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)

        # [0x00435D78] -> P_MGR_PTR
        # [P_MGR_PTR] -> first node (or 0)
        uc.mem_write(0x00435D78, struct.pack("<I", P_MGR_PTR))

        if not nodes:
            uc.mem_write(P_MGR_PTR, struct.pack("<I", 0))
        else:
            first_addr = NODE_BASE
            uc.mem_write(P_MGR_PTR, struct.pack("<I", first_addr))
            for i, (f2a2, f2, f6) in enumerate(nodes):
                curr = NODE_BASE + i * 0x400
                nxt = (NODE_BASE + (i + 1) * 0x400) if (i + 1 < len(nodes)) else 0
                uc.mem_write(curr + 0x2A2, struct.pack("<h", f2a2))
                uc.mem_write(curr + 2, struct.pack("<H", f2))
                uc.mem_write(curr + 6, struct.pack("<H", f6))
                uc.mem_write(curr + 0x2A4, struct.pack("<I", nxt))

        call_idx = 0
        def on_b6e44(uc, address, size, user_data):
            nonlocal call_idx
            res = b6e44_results[call_idx] if call_idx < len(b6e44_results) else 0
            call_idx += 1
            uc.reg_write(UC_ARM_REG_R0, res)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        h_call = uc.hook_add(UC_HOOK_CODE, on_b6e44, None, 0x002B6E44, 0x002B6E44)

        sp = STACK_BASE + STACK_SIZE - 0x1000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, 0x00200000)

        def on_exit(uc, address, size, user_data):
            uc.emu_stop()

        h_exit = uc.hook_add(UC_HOOK_CODE, on_exit, None, 0x00200000, 0x00200000)
        uc.emu_start(addr, 0x00200000, timeout=1000000)
        uc.hook_del(h_exit)
        uc.hook_del(h_call)

        return uc.reg_read(UC_ARM_REG_R0)

    test_scenarios = [
        ([], []),  # empty list -> returns 0
        ([(-1, 1, 0)], []),  # field_2a2 < 0 -> returns 0
        ([(0, 2, 0)], []),   # field_2 != 1 -> returns 0
        ([(0, 1, 1)], []),   # field_6 & 1 != 0 -> returns 0
        ([(0, 1, 0)], [0]),  # helper returns 0 -> returns 0
        ([(0, 1, 0)], [1]),  # helper returns 1 -> returns 1
        ([(-1, 1, 0), (0, 2, 0), (0, 1, 0)], [1]), # third node matches -> returns 1
        ([(0, 1, 2), (0, 1, 4)], [0, 1]), # first returns 0, second returns 1 -> returns 1
    ]

    for nodes, b_res in test_scenarios:
        orig_r0 = run_one(orig, nodes, b_res)
        comp_r0 = run_one(staged, nodes, b_res)
        assert orig_r0 == comp_r0, f"Mismatch: nodes={nodes}, b_res={b_res} -> orig={orig_r0}, comp={comp_r0}"

    print("script_vm_func_00229a34: PASS")


def test_0022a2b0():
    print("--- Testing script_vm_func_0022a2b0 ---")
    addr = 0x0022A2B0
    size = 116
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("script_vm_func_0022a2b0", ROOT / "build")
    symbol_map = {
        "engine_func_002c4b30": 0x002C4B30,
        "engine_func_002a71c0": 0x002A71C0,
        "script_vm_func_00234d4c": 0x00234D4C,
    }
    staged = stage_body(comp, relocs, addr, symbol_map)

    OBJ_VAL = 0x20005555

    def run_one(c_bytes, a0, a1, a2, a3, ret_2a71c0):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)

        # [0x00433130] = OBJ_VAL
        uc.mem_write(0x00433130, struct.pack("<I", OBJ_VAL))

        calls = []

        def on_2c4b30(uc, address, size, user_data):
            dst = uc.reg_read(UC_ARM_REG_R0)
            sz = uc.reg_read(UC_ARM_REG_R1)
            calls.append(("2c4b30", sz))
            uc.mem_write(dst, b"\x00" * sz)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def on_2a71c0(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            r1 = uc.reg_read(UC_ARM_REG_R1)
            r2 = uc.reg_read(UC_ARM_REG_R2)
            r3 = uc.reg_read(UC_ARM_REG_R3)
            calls.append(("2a71c0", r0, r1, r2))
            uc.reg_write(UC_ARM_REG_R0, ret_2a71c0)
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        def on_234d4c(uc, address, size, user_data):
            r0 = uc.reg_read(UC_ARM_REG_R0)
            r1 = uc.reg_read(UC_ARM_REG_R1)
            r2 = uc.reg_read(UC_ARM_REG_R2)
            r3 = uc.reg_read(UC_ARM_REG_R3)
            sp = uc.reg_read(UC_ARM_REG_SP)
            # read stack params
            stack_args = struct.unpack("<III", uc.mem_read(sp, 12))
            calls.append(("234d4c", r0, r2, r3, stack_args))
            lr = uc.reg_read(UC_ARM_REG_LR)
            uc.reg_write(UC_ARM_REG_PC, lr)

        h_c = uc.hook_add(UC_HOOK_CODE, on_2c4b30, None, 0x002C4B30, 0x002C4B30)
        h_a = uc.hook_add(UC_HOOK_CODE, on_2a71c0, None, 0x002A71C0, 0x002A71C0)
        h_d = uc.hook_add(UC_HOOK_CODE, on_234d4c, None, 0x00234D4C, 0x00234D4C)

        sp = STACK_BASE + STACK_SIZE - 0x1000
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, 0x00200000)
        uc.reg_write(UC_ARM_REG_R0, a0)
        uc.reg_write(UC_ARM_REG_R1, a1)
        uc.reg_write(UC_ARM_REG_R2, a2)
        uc.reg_write(UC_ARM_REG_R3, a3)

        def on_exit(uc, address, size, user_data):
            uc.emu_stop()

        h_exit = uc.hook_add(UC_HOOK_CODE, on_exit, None, 0x00200000, 0x00200000)
        uc.emu_start(addr, 0x00200000, timeout=1000000)
        uc.hook_del(h_exit)
        uc.hook_del(h_c)
        uc.hook_del(h_a)
        uc.hook_del(h_d)

        return calls

    cases = [
        (0x10, 0x20, 0x30, 0x40, 0), # 2a71c0 returns 0 -> no call to 234d4c
        (0x10, 0x20, 0x30, 0x40, 1), # 2a71c0 returns 1 -> calls 234d4c
        (0x1234, 0x5678, 0x9ABC, 0xDEF0, 1),
    ]

    for a0, a1, a2, a3, ret in cases:
        orig_calls = run_one(orig, a0, a1, a2, a3, ret)
        comp_calls = run_one(staged, a0, a1, a2, a3, ret)
        assert orig_calls == comp_calls, f"Mismatch: calls orig={orig_calls}, comp={comp_calls}"

    print("script_vm_func_0022a2b0: PASS")


if __name__ == "__main__":
    test_00226d54()
    test_00227c48()
    test_00228338()
    test_00229a34()
    test_0022a2b0()
    print("\nALL 5 FUNCTIONS PASSED 100% DIFFERENTIAL VERIFICATION!")
