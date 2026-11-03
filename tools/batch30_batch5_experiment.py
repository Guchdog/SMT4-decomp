#!/usr/bin/env python3
"""Differential test for batch 30 part 5:
- func_002b7584 (0x002B7584, 152 B)
- engine_func_002baacc (0x002BAACC, 144 B)
- ui_func_002bf0a8 (0x002BF0A8, 152 B)
- engine_func_0029bddc (0x0029BDDC, 140 B)
- engine_func_0029957c (0x0029957C, 144 B)
"""

from __future__ import annotations

from pathlib import Path
import struct
import sys

from unicorn import (
    Uc,
    UC_ARCH_ARM,
    UC_MODE_ARM,
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
    UC_ARM_REG_S0,
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
SOURCE = ROOT / "src/engine/leaf_batch30_c.cpp"

def load_original_bytes(addr: int, size: int) -> bytes:
    with open(ORIG_BIN, "rb") as f:
        f.seek(addr - CODE_BASE)
        return f.read(size)

def compile_function(func_name: str, out: Path, source: Path = SOURCE):
    global COMPILED_FUNCTIONS
    if COMPILED_FUNCTIONS is None:
        obj = out / "leaf_batch30_c.o"
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

    uc.mem_map(STACK_BASE, STACK_SIZE)
    # Extra data page
    uc.mem_map(0x20000000, 0x20000)
    # Map high global region 0x004D0000 - 0x004F0000
    uc.mem_map(0x004D0000, 0x20000)
    return uc

def test_002b7584():
    print("--- Testing func_002b7584 ---")
    addr = 0x002B7584
    size = 152
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("func_002b7584", ROOT / "build")
    staged = stage_body(comp, relocs, addr, {})

    OUT = 0x20000000
    IN = 0x20000100

    def run_one(c_bytes, in_floats):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)

        # Pack 12 floats for input
        uc.mem_write(IN, struct.pack("<12f", *in_floats))
        uc.mem_write(OUT, b"\x00" * 32)

        sp = STACK_BASE + STACK_SIZE - 0x100
        lr = addr + len(c_bytes)
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, lr)
        uc.reg_write(UC_ARM_REG_R0, OUT)
        uc.reg_write(UC_ARM_REG_R1, IN)

        def hook_mem_unmapped(uc, access, address, size, value, user_data):
            pc = uc.reg_read(UC_ARM_REG_R0) # or PC
            print(f"FAULT: access={access}, addr=0x{address:08X}, size={size}, val=0x{value:08X}")
            return False

        from unicorn import UC_HOOK_MEM_UNMAPPED
        uc.hook_add(UC_HOOK_MEM_UNMAPPED, hook_mem_unmapped)

        uc.emu_start(addr, lr, timeout=3000000)
        out_bytes = uc.mem_read(OUT, 24)
        return struct.unpack("<6f", out_bytes)

    test_vectors = [
        # in[0], in[1], in[2], in[3], in[4], in[5], in[6], in[7], in[8], in[9], in[10], in[11]
        [2.0, 0.0, 0.5, 0.0, 0.0, 1.0, -0.5, 0.0, 0.0, 0.0, 3.0, 12.0],
        [4.0, 0.0, 1.5, 0.0, 0.0, 2.5,  2.0, 0.0, 0.0, 0.0, 5.0, 20.0],
        [1.0, 0.0, -1.0, 0.0, 0.0, 0.5, 0.0, 0.0, 0.0, 0.0, 2.0, 8.0],
        [5.0, 0.0, 2.0, 0.0, 0.0, 3.0, -1.5, 0.0, 0.0, 0.0, 6.0, 30.0],
    ]

    for vec in test_vectors:
        o = run_one(orig, vec)
        c = run_one(staged, vec)
        for i in range(6):
            assert abs(o[i] - c[i]) < 1e-4, f"Mismatch at index {i}: {o} vs {c}"
    print("func_002b7584: PASS")

def test_002baacc():
    print("--- Testing engine_func_002baacc ---")
    addr = 0x002BAACC
    size = 144
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("engine_func_002baacc", ROOT / "build")
    symbol_map = {
        "camp_func_002c3344": 0x002C3344,
        "camp_func_002c32f8": 0x002C32F8,
    }
    staged = stage_body(comp, relocs, addr, symbol_map)

    OBJ = 0x20000000
    OBJ_SIZE = 0x500

    def run_one(c_bytes):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)

        # Pre-fill obj with garbage
        uc.mem_write(OBJ, b"\xAA" * OBJ_SIZE)

        sp = STACK_BASE + STACK_SIZE - 0x100
        lr = addr + len(c_bytes)
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, lr)
        uc.reg_write(UC_ARM_REG_R0, OBJ)
        uc.reg_write(UC_ARM_REG_R4, 0x11111111)
        uc.reg_write(UC_ARM_REG_R5, 0x22222222)

        def hook_mem_unmapped(uc, access, address, size, value, user_data):
            pc = uc.reg_read(UC_ARM_REG_R0) # or PC
            print(f"FAULT: access={access}, addr=0x{address:08X}, size={size}, val=0x{value:08X}")
            return False

        from unicorn import UC_HOOK_MEM_UNMAPPED
        uc.hook_add(UC_HOOK_MEM_UNMAPPED, hook_mem_unmapped)

        uc.emu_start(addr, lr, timeout=3000000)
        return {
            "obj": uc.mem_read(OBJ, OBJ_SIZE),
            "r4": uc.reg_read(UC_ARM_REG_R4),
            "r5": uc.reg_read(UC_ARM_REG_R5),
        }

    o = run_one(orig)
    c = run_one(staged)
    assert o["obj"] == c["obj"], "002baacc obj state mismatch"
    assert o["r4"] == c["r4"], f"002baacc r4 mismatch: {o['r4']} vs {c['r4']}"
    assert o["r5"] == c["r5"], f"002baacc r5 mismatch: {o['r5']} vs {c['r5']}"
    print("engine_func_002baacc: PASS")

def test_002bf0a8():
    print("--- Testing ui_func_002bf0a8 ---")
    addr = 0x002BF0A8
    size = 152
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("ui_func_002bf0a8", ROOT / "build")
    symbol_map = {
        "engine_func_002c4b30": 0x002C4B30,
    }
    staged = stage_body(comp, relocs, addr, symbol_map)

    SPRITE = 0x20000000
    GROUP = 0x20000200

    def run_one(c_bytes, p1, p2, p3, scale, panel):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)

        # Pre-fill sprite with garbage
        uc.mem_write(SPRITE, b"\x55" * 0x100)

        # Group data
        group_words = [i * 0x11111111 for i in range(16)]
        uc.mem_write(GROUP, struct.pack("<16I", *group_words))

        sp = STACK_BASE + STACK_SIZE - 0x100
        # Stack args: group, panel
        uc.mem_write(sp, struct.pack("<II", GROUP, panel))

        lr = addr + len(c_bytes)
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, lr)
        uc.reg_write(UC_ARM_REG_R0, SPRITE)
        uc.reg_write(UC_ARM_REG_R1, p1)
        uc.reg_write(UC_ARM_REG_R2, p2)
        uc.reg_write(UC_ARM_REG_R3, p3)
        # S0 = scale
        scale_bytes = struct.pack("<f", scale)
        scale_int = struct.unpack("<I", scale_bytes)[0]
        uc.reg_write(UC_ARM_REG_S0, scale_int)

        uc.reg_write(UC_ARM_REG_R4, 0x11111111)
        uc.reg_write(UC_ARM_REG_R5, 0x22222222)
        uc.reg_write(UC_ARM_REG_R6, 0x33333333)
        uc.reg_write(UC_ARM_REG_R7, 0x44444444)
        uc.reg_write(UC_ARM_REG_R8, 0x55555555)
        uc.reg_write(UC_ARM_REG_SB, 0x66666666)
        uc.reg_write(UC_ARM_REG_SL, 0x77777777)

        def hook_mem_unmapped(uc, access, address, size, value, user_data):
            pc = uc.reg_read(UC_ARM_REG_R0) # or PC
            print(f"FAULT: access={access}, addr=0x{address:08X}, size={size}, val=0x{value:08X}")
            return False

        from unicorn import UC_HOOK_MEM_UNMAPPED
        uc.hook_add(UC_HOOK_MEM_UNMAPPED, hook_mem_unmapped)

        uc.emu_start(addr, lr, timeout=3000000)
        return {
            "sprite": uc.mem_read(SPRITE, 0x8C),
            "r4": uc.reg_read(UC_ARM_REG_R4),
            "r5": uc.reg_read(UC_ARM_REG_R5),
            "r6": uc.reg_read(UC_ARM_REG_R6),
            "r7": uc.reg_read(UC_ARM_REG_R7),
            "r8": uc.reg_read(UC_ARM_REG_R8),
            "sb": uc.reg_read(UC_ARM_REG_SB),
            "sl": uc.reg_read(UC_ARM_REG_SL),
        }

    cases = [
        (1, 2, 3, 1.5, 4),
        (10, 20, 30, 2.0, 7),
        (0xFF, 0xAA, 0xBB, 0.5, 12),
    ]
    for p1, p2, p3, scale, panel in cases:
        o = run_one(orig, p1, p2, p3, scale, panel)
        c = run_one(staged, p1, p2, p3, scale, panel)
        assert o["sprite"] == c["sprite"], f"002bf0a8 sprite mismatch: {o['sprite']} vs {c['sprite']}"
        assert o["r4"] == c["r4"], f"002bf0a8 r4 mismatch"
        assert o["r5"] == c["r5"], f"002bf0a8 r5 mismatch"
        assert o["r6"] == c["r6"], f"002bf0a8 r6 mismatch"
        assert o["r7"] == c["r7"], f"002bf0a8 r7 mismatch"
        assert o["r8"] == c["r8"], f"002bf0a8 r8 mismatch"
        assert o["sb"] == c["sb"], f"002bf0a8 sb mismatch"
        assert o["sl"] == c["sl"], f"002bf0a8 sl mismatch"
    print("ui_func_002bf0a8: PASS")

def test_0029bddc():
    print("--- Testing engine_func_0029bddc ---")
    addr = 0x0029BDDC
    size = 140
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("engine_func_0029bddc", ROOT / "build")
    symbol_map = {
        "sub_002A135C": 0x002A135C,
        "sub_002B0434": 0x002B0434,
        "sub_002B0418": 0x002B0418,
        "sub_001181B0": 0x001181B0,
        "sub_00138330": 0x00138330,
        "sub_002B2B78": 0x002B2B78,
        "sub_002A9498": 0x002A9498,
        "sub_002B2928": 0x002B2928,
        "sub_002B2814": 0x002B2814,
    }
    staged = stage_body(comp, relocs, addr, symbol_map)

    NODE = 0x20000000
    SUBNODE = 0x20000100
    CTX = 0x20000200
    RES4 = 0x20000300
    RES2 = 0x20000400

    def run_one(c_bytes, val):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)

        # Pre-initialize node and subnode
        uc.mem_write(NODE, struct.pack("<III", 0, 0, SUBNODE))
        uc.mem_write(SUBNODE, struct.pack("<III", 0, 0, 0))

        # Stubs
        # 0x2a135c: return NODE
        uc.mem_write(0x002A135C, (
            b"\x00\x00\x9f\xe5" # ldr r0, [pc, #0]
            b"\x1e\xff\x2f\xe1" # bx lr
            + struct.pack("<I", NODE)
        ))
        # 0x2b0434: return RES4
        uc.mem_write(0x002B0434, (
            b"\x00\x00\x9f\xe5" # ldr r0, [pc, #0]
            b"\x1e\xff\x2f\xe1" # bx lr
            + struct.pack("<I", RES4)
        ))
        # 0x2b0418: bx lr
        uc.mem_write(0x002B0418, b"\x1e\xff\x2f\xe1")
        # 0x1181b0: bx lr
        uc.mem_write(0x001181B0, b"\x1e\xff\x2f\xe1")
        # 0x138330: str r2, [r1] where r2 = 0x55; bx lr
        uc.mem_write(0x00138330, b"\x55\x20\xa0\xe3\x00\x20\x81\xe5\x1e\xff\x2f\xe1")
        # 0x2b2b78: return RES2
        uc.mem_write(0x002B2B78, (
            b"\x00\x00\x9f\xe5" # ldr r0, [pc, #0]
            b"\x1e\xff\x2f\xe1" # bx lr
            + struct.pack("<I", RES2)
        ))
        # 0x2a9498: bx lr
        uc.mem_write(0x002A9498, b"\x1e\xff\x2f\xe1")
        # 0x2b2928: bx lr
        uc.mem_write(0x002B2928, b"\x1e\xff\x2f\xe1")
        # 0x2b2814: bx lr
        uc.mem_write(0x002B2814, b"\x1e\xff\x2f\xe1")

        sp = STACK_BASE + STACK_SIZE - 0x100
        lr = addr + len(c_bytes)
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, lr)
        uc.reg_write(UC_ARM_REG_R0, CTX)
        uc.reg_write(UC_ARM_REG_R1, val)

        uc.reg_write(UC_ARM_REG_R4, 0x11111111)
        uc.reg_write(UC_ARM_REG_R5, 0x22222222)
        uc.reg_write(UC_ARM_REG_R6, 0x33333333)
        uc.reg_write(UC_ARM_REG_R7, 0x44444444)

        def hook_mem_unmapped(uc, access, address, size, value, user_data):
            pc = uc.reg_read(UC_ARM_REG_R0) # or PC
            print(f"FAULT: access={access}, addr=0x{address:08X}, size={size}, val=0x{value:08X}")
            return False

        from unicorn import UC_HOOK_MEM_UNMAPPED
        uc.hook_add(UC_HOOK_MEM_UNMAPPED, hook_mem_unmapped)

        uc.emu_start(addr, lr, timeout=3000000)
        return {
            "ret": uc.reg_read(UC_ARM_REG_R0),
            "node": uc.mem_read(NODE, 12),
            "subnode": uc.mem_read(SUBNODE, 12),
            "r4": uc.reg_read(UC_ARM_REG_R4),
            "r5": uc.reg_read(UC_ARM_REG_R5),
            "r6": uc.reg_read(UC_ARM_REG_R6),
            "r7": uc.reg_read(UC_ARM_REG_R7),
        }

    for v in [0x1234, 0x5678, 0x9ABC]:
        o = run_one(orig, v)
        c = run_one(staged, v)
        assert o == c, f"0029bddc (val={v}) mismatch: {o} vs {c}"
    print("engine_func_0029bddc: PASS")

def test_0029957c():
    print("--- Testing engine_func_0029957c ---")
    addr = 0x0029957C
    size = 144
    orig = load_original_bytes(addr, size)
    comp, relocs = compile_function("engine_func_0029957c", ROOT / "build")
    symbol_map = {
        "engine_func_002946f4": 0x002946F4,
    }
    staged = stage_body(comp, relocs, addr, symbol_map)

    PTR_SLOT = 0x0044E140
    GLOBAL_OBJ = 0x20000000
    HANDLE_VAL = 0xCAFEBABE

    def run_one(c_bytes, mode):
        uc = setup_uc()
        uc.mem_write(addr, c_bytes)

        # Set up PTR_SLOT + 4 -> GLOBAL_OBJ
        uc.mem_write(PTR_SLOT, struct.pack("<II", 0, GLOBAL_OBJ))

        # Pre-fill GLOBAL_OBJ
        obj_data = bytearray(0x2000)
        # Put handle at 0x1E80
        struct.pack_into("<I", obj_data, 0x1E80, HANDLE_VAL)
        # Put non-zero values at 0x10 and 0x12DC to test write
        struct.pack_into("<I", obj_data, 0x10, 0xDEADBEEF)
        struct.pack_into("<I", obj_data, 0x12DC, 0xFEEDFACE)
        uc.mem_write(GLOBAL_OBJ, bytes(obj_data))

        # Stub 0x002946F4: records args into 0x20010000 and returns
        ARG_LOG = 0x20010000
        uc.mem_write(ARG_LOG, struct.pack("<III", 0, 0, 0))
        # mov ip, 0x20010000; stm ip, {r0, r1, r2}; bx lr
        stub = (
            b"\x04\xc0\x9f\xe5" # ldr ip, [pc, #4] -> ARG_LOG at offset 12
            b"\x07\x00\x8c\xe8" # stm ip, {r0, r1, r2}
            b"\x1e\xff\x2f\xe1" # bx lr
            + struct.pack("<I", ARG_LOG)
        )
        uc.mem_write(0x002946F4, stub)

        sp = STACK_BASE + STACK_SIZE - 0x100
        lr = addr + len(c_bytes)
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, lr)
        uc.reg_write(UC_ARM_REG_R0, mode)
        uc.reg_write(UC_ARM_REG_R4, 0x11111111)

        def hook_mem_unmapped(uc, access, address, size, value, user_data):
            pc = uc.reg_read(UC_ARM_REG_R0) # or PC
            print(f"FAULT: access={access}, addr=0x{address:08X}, size={size}, val=0x{value:08X}")
            return False

        from unicorn import UC_HOOK_MEM_UNMAPPED
        uc.hook_add(UC_HOOK_MEM_UNMAPPED, hook_mem_unmapped)

        uc.emu_start(addr, lr, timeout=3000000)
        return {
            "arg_log": uc.mem_read(ARG_LOG, 12),
            "val_10": struct.unpack("<I", uc.mem_read(GLOBAL_OBJ + 0x10, 4))[0],
            "val_12dc": struct.unpack("<I", uc.mem_read(GLOBAL_OBJ + 0x12DC, 4))[0],
            "r4": uc.reg_read(UC_ARM_REG_R4),
        }

    for m in [0, 1, 2, 3]:
        o = run_one(orig, m)
        c = run_one(staged, m)
        assert o == c, f"0029957c (mode={m}) mismatch: {o} vs {c}"
    print("engine_func_0029957c: PASS")

def main():
    test_002b7584()
    test_002baacc()
    test_002bf0a8()
    test_0029bddc()
    test_0029957c()
    print("\nALL 5 FUNCTIONS IN BATCH 5 PASSED DIFFERENTIAL VERIFICATION!")

if __name__ == "__main__":
    main()
