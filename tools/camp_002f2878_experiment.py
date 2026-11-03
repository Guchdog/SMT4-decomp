#!/usr/bin/env python3
"""Differential test for camp_func_002f2878 (0x002F2878).

Validates that reconstructed C++ matches original ARM binary across all
comparison branches:
- flags_b has bits not in flags_a -> returns 1
- flags_a has bits not in flags_b -> returns -1
- flags identical, rec_b[2] != rec_a[2] -> returns rec_b[2] - rec_a[2]
- flags and byte 2 identical, rec_a[3] != rec_b[3] -> returns rec_a[3] - rec_b[3]
- all previous identical, *(u16*)rec_b != *(u16*)rec_a -> returns rec_b[0] - rec_a[0]
- completely identical -> returns 0
- boundary and signed difference cases
- verifies preservation of non-volatile registers (r4, r5, r6, r7, r8).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import struct
import sys

from unicorn import (
    Uc,
    UC_ARCH_ARM,
    UC_MODE_ARM,
)
from unicorn.arm_const import (
    UC_ARM_REG_R0,
    UC_ARM_REG_R1,
    UC_ARM_REG_R2,
    UC_ARM_REG_R3,
    UC_ARM_REG_R4,
    UC_ARM_REG_R5,
    UC_ARM_REG_R6,
    UC_ARM_REG_R7,
    UC_ARM_REG_R8,
    UC_ARM_REG_SP,
    UC_ARM_REG_LR,
    UC_ARM_REG_PC,
)

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k

ORIG_BIN = ROOT / "extracted/exefs/code.bin"
ORIG_ADDR = 0x002F2878
ORIG_SIZE = 128

STACK_BASE = 0x10080000
STACK_SIZE = 0x10000
CODE_BASE = 0x00100000
CODE_SIZE = 0x00380000

STUB_FLAGS = 0x0029ED08
STUB_RECORD = 0x002B9364

SOURCE = ROOT / "src/engine/leaf_batch30_c.cpp"

SYMBOL_MAP = {
    "camp_func_0029ed08": STUB_FLAGS,
    "camp_func_002b9364": STUB_RECORD,
}


def load_original_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as f:
        f.seek(ORIG_ADDR - 0x00100000)
        return f.read(ORIG_SIZE)


def compile_body(out: Path, source: Path = SOURCE):
    obj = out / "leaf_batch30_c.o"
    result = compile_tu_armv6k(source, obj, ROOT)
    if result.returncode != 0:
        raise RuntimeError(result.stderr)
    functions = extract_elf_functions_detailed(obj)
    if "camp_func_002f2878" not in functions:
        raise RuntimeError("camp_func_002f2878 not in object")
    body, relocs = functions["camp_func_002f2878"]
    return body, relocs


def stage_body(body: bytes, relocs, target_addr: int) -> bytes:
    data = bytearray(body)
    for reloc in relocs:
        sym = reloc.symbol_name
        if sym not in SYMBOL_MAP:
            raise RuntimeError(f"Unmapped relocation: {sym}")
        stub_addr = SYMBOL_MAP[sym]
        rel_off = stub_addr - (target_addr + reloc.offset + 8)
        imm24 = (rel_off >> 2) & 0x00FFFFFF
        branch_ins = 0xEB000000 | imm24
        struct.pack_into("<I", data, reloc.offset, branch_ins)
    return bytes(data)


def run_single(code_bytes: bytes, entry_addr: int, id_a: int, id_b: int,
               flags_map: dict[int, int], record_map: dict[int, tuple[int, int, int]]):
    """
    record_map[id] = (u16_val, byte2_val, byte3_val)
    """
    uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc.mem_map(CODE_BASE, CODE_SIZE)
    uc.mem_map(STACK_BASE, STACK_SIZE)

    DATA_PAGE = 0x10000000
    uc.mem_map(DATA_PAGE, 0x20000)

    # Write code under test
    uc.mem_write(entry_addr, code_bytes)

    # Set up tables / stubs for callees
    # STUB_FLAGS (0x0029ED08):
    # Reads r0 (id). Returns flags from a lookup table in DATA_PAGE
    FLAGS_TABLE = DATA_PAGE + 0x1000  # array of u32 indexed by u16 id
    for k, v in flags_map.items():
        uc.mem_write(FLAGS_TABLE + k * 4, struct.pack("<I", v))

    # STUB_FLAGS code:
    # ldr r1, =FLAGS_TABLE; ldr r0, [r1, r0, lsl #2]; bx lr
    flags_stub = struct.pack(
        "<IIII",
        0xe59f1004,  # ldr r1, [pc, #4]
        0xe7910100,  # ldr r0, [r1, r0, lsl #2]
        0xe12fff1e,  # bx lr
        FLAGS_TABLE,
    )
    uc.mem_write(STUB_FLAGS, flags_stub)

    # STUB_RECORD (0x002B9364):
    # Reads r0 (id). Returns pointer to record struct (u16, u8, u8)
    REC_TABLE = DATA_PAGE + 0x5000  # records: 4 bytes each: u16 id_field, u8 b2, u8 b3
    for k, (u16_val, b2, b3) in record_map.items():
        rec_addr = REC_TABLE + k * 4
        uc.mem_write(rec_addr, struct.pack("<HBB", u16_val, b2, b3))

    # STUB_RECORD code:
    # ldr r1, =REC_TABLE; add r0, r1, r0, lsl #2; bx lr
    rec_stub = struct.pack(
        "<IIII",
        0xe59f1004,  # ldr r1, [pc, #4]
        0xe0810100,  # add r0, r1, r0, lsl #2
        0xe12fff1e,  # bx lr
        REC_TABLE,
    )
    uc.mem_write(STUB_RECORD, rec_stub)

    # Arguments: pointers to id_a and id_b in memory
    PTR_A = DATA_PAGE + 0x100
    PTR_B = DATA_PAGE + 0x108
    uc.mem_write(PTR_A, struct.pack("<H", id_a))
    uc.mem_write(PTR_B, struct.pack("<H", id_b))

    sp = STACK_BASE + 0x8000
    lr = 0x00100000  # exit address

    SENTINEL_R4 = 0x44444444
    SENTINEL_R5 = 0x55555555
    SENTINEL_R6 = 0x66666666
    SENTINEL_R7 = 0x77777777
    SENTINEL_R8 = 0x88888888

    uc.reg_write(UC_ARM_REG_R0, PTR_A)
    uc.reg_write(UC_ARM_REG_R1, PTR_B)
    uc.reg_write(UC_ARM_REG_R4, SENTINEL_R4)
    uc.reg_write(UC_ARM_REG_R5, SENTINEL_R5)
    uc.reg_write(UC_ARM_REG_R6, SENTINEL_R6)
    uc.reg_write(UC_ARM_REG_R7, SENTINEL_R7)
    uc.reg_write(UC_ARM_REG_R8, SENTINEL_R8)
    uc.reg_write(UC_ARM_REG_SP, sp)
    uc.reg_write(UC_ARM_REG_LR, lr)
    uc.reg_write(UC_ARM_REG_PC, entry_addr)

    # 1000 instructions max
    uc.emu_start(entry_addr, lr, timeout=0, count=1000)

    # Read signed r0
    raw_r0 = uc.reg_read(UC_ARM_REG_R0)
    # Convert to signed 32-bit int
    if raw_r0 >= 0x80000000:
        ret_r0 = raw_r0 - 0x100000000
    else:
        ret_r0 = raw_r0

    regs = {
        "r0": ret_r0,
        "r4": uc.reg_read(UC_ARM_REG_R4),
        "r5": uc.reg_read(UC_ARM_REG_R5),
        "r6": uc.reg_read(UC_ARM_REG_R6),
        "r7": uc.reg_read(UC_ARM_REG_R7),
        "r8": uc.reg_read(UC_ARM_REG_R8),
    }

    assert regs["r4"] == SENTINEL_R4, f"r4 clobbered: {hex(regs['r4'])}"
    assert regs["r5"] == SENTINEL_R5, f"r5 clobbered: {hex(regs['r5'])}"
    assert regs["r6"] == SENTINEL_R6, f"r6 clobbered: {hex(regs['r6'])}"
    assert regs["r7"] == SENTINEL_R7, f"r7 clobbered: {hex(regs['r7'])}"
    assert regs["r8"] == SENTINEL_R8, f"r8 clobbered: {hex(regs['r8'])}"

    return regs


def main():
    parser = argparse.ArgumentParser(description="Differential test for camp_func_002f2878")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    out_dir = ROOT / "build"
    out_dir.mkdir(exist_ok=True)

    orig_bytes = load_original_bytes()
    compiled_body, relocs = compile_body(out_dir)
    staged_compiled = stage_body(compiled_body, relocs, ORIG_ADDR)

    # Build test cases
    test_cases = []

    # Branch 1: flags_b has unique bit -> return 1
    test_cases.append({
        "name": "flags_b_unique_bit",
        "id_a": 1, "id_b": 2,
        "flags": {1: 0x00, 2: 0x01},
        "records": {1: (10, 0, 0), 2: (10, 0, 0)},
    })
    test_cases.append({
        "name": "flags_b_multiple_unique",
        "id_a": 1, "id_b": 2,
        "flags": {1: 0x10, 2: 0x30},
        "records": {1: (10, 0, 0), 2: (10, 0, 0)},
    })

    # Branch 2: flags_a has unique bit -> return -1
    test_cases.append({
        "name": "flags_a_unique_bit",
        "id_a": 1, "id_b": 2,
        "flags": {1: 0x02, 2: 0x00},
        "records": {1: (10, 0, 0), 2: (10, 0, 0)},
    })
    test_cases.append({
        "name": "flags_a_multiple_unique",
        "id_a": 1, "id_b": 2,
        "flags": {1: 0xFF, 2: 0x0F},
        "records": {1: (10, 0, 0), 2: (10, 0, 0)},
    })

    # Branch 3: flags equal, rec_b[2] != rec_a[2] -> diff = rec_b[2] - rec_a[2]
    test_cases.append({
        "name": "rec_b2_greater",
        "id_a": 1, "id_b": 2,
        "flags": {1: 0x05, 2: 0x05},
        "records": {1: (100, 5, 10), 2: (200, 25, 10)},
    })
    test_cases.append({
        "name": "rec_b2_less",
        "id_a": 1, "id_b": 2,
        "flags": {1: 0x05, 2: 0x05},
        "records": {1: (100, 50, 10), 2: (200, 10, 10)},
    })

    # Branch 4: flags and byte 2 equal, rec_a[3] != rec_b[3] -> diff = rec_a[3] - rec_b[3]
    test_cases.append({
        "name": "rec_b3_less",
        "id_a": 1, "id_b": 2,
        "flags": {1: 0x05, 2: 0x05},
        "records": {1: (100, 20, 80), 2: (200, 20, 30)},
    })
    test_cases.append({
        "name": "rec_b3_greater",
        "id_a": 1, "id_b": 2,
        "flags": {1: 0x05, 2: 0x05},
        "records": {1: (100, 20, 10), 2: (200, 20, 75)},
    })

    # Branch 5: flags, b2, b3 equal, u16 diff
    test_cases.append({
        "name": "u16_diff_positive",
        "id_a": 1, "id_b": 2,
        "flags": {1: 0x05, 2: 0x05},
        "records": {1: (50, 15, 25), 2: (150, 15, 25)},
    })
    test_cases.append({
        "name": "u16_diff_negative",
        "id_a": 1, "id_b": 2,
        "flags": {1: 0x05, 2: 0x05},
        "records": {1: (500, 15, 25), 2: (100, 15, 25)},
    })
    test_cases.append({
        "name": "u16_equal_all_equal",
        "id_a": 1, "id_b": 2,
        "flags": {1: 0x05, 2: 0x05},
        "records": {1: (300, 15, 25), 2: (300, 15, 25)},
    })

    # Additional combinatorial cases
    for b2_a in [0, 1, 127, 255]:
        for b2_b in [0, 1, 128, 255]:
            test_cases.append({
                "name": f"comb_b2_{b2_a}_{b2_b}",
                "id_a": 10, "id_b": 20,
                "flags": {10: 0x1234, 20: 0x1234},
                "records": {10: (0x5555, b2_a, 42), 20: (0x5555, b2_b, 42)},
            })

    passed = 0
    total = len(test_cases)
    results = []

    for case in test_cases:
        orig_res = run_single(
            orig_bytes, ORIG_ADDR, case["id_a"], case["id_b"],
            case["flags"], case["records"]
        )
        comp_res = run_single(
            staged_compiled, ORIG_ADDR, case["id_a"], case["id_b"],
            case["flags"], case["records"]
        )

        match = (orig_res["r0"] == comp_res["r0"])
        if not match:
            print(f"FAILED case {case['name']}: orig={orig_res['r0']}, comp={comp_res['r0']}")
        assert match, f"Case {case['name']} failed"
        passed += 1
        results.append({
            "case": case["name"],
            "expected_r0": orig_res["r0"],
            "got_r0": comp_res["r0"],
            "status": "PASS"
        })

    summary = {
        "function": "camp_func_002f2878",
        "address": f"0x{ORIG_ADDR:08X}",
        "total_cases": total,
        "passed_cases": passed,
        "status": "PASS" if passed == total else "FAIL",
    }

    if args.json:
        print(json.dumps({"summary": summary, "results": results}, indent=2))
    else:
        print(f"Differential test passed: {passed}/{total} cases matched original binary exactly!")

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
