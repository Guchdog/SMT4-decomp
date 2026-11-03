#!/usr/bin/env python3
"""Differential test for camp_func_002960d4 (0x002960D4).

Validates that reconstructed C++ matches original ARM binary across all
branch combinations:
- diff <= 0 (clamp to 100% scale)
- 0 < diff <= 10 (scale read from table 9 subtable 2)
- diff > 10 (clamped to index 10 in subtable 2)
- various base values and scale multipliers
- verifies return value (base_val * scale / 100)
- verifies non-volatile registers (r4, r5, r6, r7, r8).
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
ORIG_ADDR = 0x002960D4
ORIG_SIZE = 128

STACK_BASE = 0x10080000
STACK_SIZE = 0x10000
CODE_BASE = 0x00100000
CODE_SIZE = 0x00380000

STUB_GET_GLOBAL_SUB = 0x002C0EC4
STUB_GET_PAYLOAD = 0x002C0E9C
STUB_CAMP_RECORD = 0x002B9364

PAYLOAD_SUB1 = 0x10010000
PAYLOAD_SUB2 = 0x10020000
RECORD_MEM = 0x10030000

SOURCE = ROOT / "src/engine/leaf_batch30_c.cpp"

SYMBOL_MAP = {
    "Tbb_GetGlobalSubTable": STUB_GET_GLOBAL_SUB,
    "Tbb_GetPayloadData": STUB_GET_PAYLOAD,
    "camp_func_002b9364": STUB_CAMP_RECORD,
}


def load_original_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as f:
        f.seek(ORIG_ADDR - 0x00100000)
        return f.read(ORIG_SIZE)


def compile_body(out: Path, source: Path = SOURCE):
    obj = out / "leaf_batch30_c.o"
    result = compile_tu_armv6k(source, obj, ROOT)
    if result.returncode != 0:
        raise RuntimeError(result.stderr or "ARMv6K translation unit compile failed")
    funcs = extract_elf_functions_detailed(obj)
    for sym_name, (body, relocs) in funcs.items():
        if "002960d4" in sym_name:
            return body, relocs, obj, sym_name
    raise KeyError("camp_func_002960d4 not found in compiled object")


def stage_body(body: bytes, relocations) -> bytes:
    fixed = bytearray(body)
    for reloc in relocations:
        site = ORIG_ADDR + reloc.offset
        target = None
        for sym_prefix, sym_addr in SYMBOL_MAP.items():
            if sym_prefix in reloc.symbol_name:
                target = sym_addr
                break
        if target is None:
            raise KeyError(f"Unmapped relocation: {reloc.symbol_name}")
        imm24 = ((target - (site + 8)) >> 2) & 0x00FFFFFF
        insn = 0xEB000000 | imm24
        struct.pack_into("<I", fixed, reloc.offset, insn)
    return bytes(fixed)


def run_test_case(code_bytes: bytes, key: int, index: int, stat_val: int, base_req: int, is_thumb: bool = False):
    uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc.mem_map(CODE_BASE, CODE_SIZE)
    uc.mem_write(ORIG_ADDR, code_bytes)

    uc.mem_map(STACK_BASE, STACK_SIZE)
    # Map heap data
    uc.mem_map(0x10000000, 0x40000)

    # Initialize subtable 1 payload: 20 u32 elements (e.g. 100, 200, 350, 500, ...)
    sub1_data = struct.pack("<20I", *[100 * (i + 1) for i in range(20)])
    uc.mem_write(PAYLOAD_SUB1, sub1_data)

    # Initialize subtable 2 payload: 12 u16 elements (percentages: 100, 110, 120, 130, ..., 200)
    sub2_data = struct.pack("<12H", *[100 + 10 * i for i in range(12)])
    uc.mem_write(PAYLOAD_SUB2, sub2_data)

    # Initialize record at RECORD_MEM: byte at offset 3 is base_req
    rec_bytes = bytearray(16)
    rec_bytes[3] = base_req & 0xFF
    uc.mem_write(RECORD_MEM, bytes(rec_bytes))

    # STUB_GET_GLOBAL_SUB: mov r0, r1; bx lr
    uc.mem_write(STUB_GET_GLOBAL_SUB, struct.pack("<II", 0xE1A00001, 0xE12FFF1E))

    # STUB_GET_PAYLOAD:
    # cmp r0, #1
    # ldreq r0, [pc, #4]
    # ldrne r0, [pc, #4]
    # bx lr
    # .word PAYLOAD_SUB1
    # .word PAYLOAD_SUB2
    payload_stub = struct.pack(
        "<IIIIII",
        0xE3500001,  # cmp r0, #1
        0x059F0004,  # ldreq r0, [pc, #4]
        0x159F0004,  # ldrne r0, [pc, #4]
        0xE12FFF1E,  # bx lr
        PAYLOAD_SUB1,
        PAYLOAD_SUB2,
    )
    uc.mem_write(STUB_GET_PAYLOAD, payload_stub)

    # STUB_CAMP_RECORD:
    # ldr r0, [pc]
    # bx lr
    # .word RECORD_MEM
    record_stub = struct.pack(
        "<III",
        0xE59F0000,
        0xE12FFF1E,
        RECORD_MEM,
    )
    uc.mem_write(STUB_CAMP_RECORD, record_stub)

    sp = STACK_BASE + 0x8000
    lr = 0x00101234
    uc.mem_write(lr, struct.pack("<I", 0xE1200070))

    uc.reg_write(UC_ARM_REG_SP, sp)
    uc.reg_write(UC_ARM_REG_LR, lr)
    uc.reg_write(UC_ARM_REG_R0, key & 0xFFFF)
    uc.reg_write(UC_ARM_REG_R1, index)
    uc.reg_write(UC_ARM_REG_R2, stat_val)
    uc.reg_write(UC_ARM_REG_R4, 0x44444444)
    uc.reg_write(UC_ARM_REG_R5, 0x55555555)
    uc.reg_write(UC_ARM_REG_R6, 0x66666666)
    uc.reg_write(UC_ARM_REG_R7, 0x77777777)
    uc.reg_write(UC_ARM_REG_R8, 0x88888888)

    try:
        uc.emu_start(ORIG_ADDR | (1 if is_thumb else 0), lr, timeout=2000000)
    except Exception as e:
        pc = uc.reg_read(UC_ARM_REG_PC)
        if pc != lr:
            raise RuntimeError(f"Emulation failed at PC={pc:#x}: {e}")

    ret_r0 = uc.reg_read(UC_ARM_REG_R0)
    r4 = uc.reg_read(UC_ARM_REG_R4)
    r5 = uc.reg_read(UC_ARM_REG_R5)
    r6 = uc.reg_read(UC_ARM_REG_R6)
    r7 = uc.reg_read(UC_ARM_REG_R7)
    r8 = uc.reg_read(UC_ARM_REG_R8)

    return {
        "ret": ret_r0,
        "r4": r4,
        "r5": r5,
        "r6": r6,
        "r7": r7,
        "r8": r8,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=ROOT / "build/agent-work/H2-semantic/camp-002960d4/run001")
    args = parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    orig_bytes = load_original_bytes()

    cases = []
    # (key, index, stat_val, base_req)
    # diff = stat_val - base_req + 1
    # 1. diff <= 0 (e.g. stat=10, base=15 -> diff = -4; stat=10, base=11 -> diff = 0)
    cases.append((1, 1, 10, 15))
    cases.append((2, 2, 10, 11))
    cases.append((3, 3, 5, 20))

    # 2. 0 < diff <= 10 (e.g. stat=15, base=15 -> diff = 1; stat=24, base=15 -> diff = 10)
    for d in range(1, 11):
        cases.append((10 + d, (d % 5) + 1, 15 + d - 1, 15))

    # 3. diff > 10 (clamp to 10; e.g. stat=30, base=15 -> diff = 16)
    cases.append((99, 1, 30, 15))
    cases.append((100, 4, 50, 10))
    cases.append((101, 5, 99, 1))

    print(f"Running {len(cases)} differential cases...")
    orig_results = []
    for k, idx, sv, br in cases:
        res = run_test_case(orig_bytes, k, idx, sv, br)
        orig_results.append(res)

    body, relocs, obj, sym_name = compile_body(args.out_dir)
    print(f"Compiled {sym_name}: {len(body)} bytes (slot {ORIG_SIZE} bytes)")
    assert len(body) <= ORIG_SIZE, f"Compiled code size {len(body)} exceeds slot {ORIG_SIZE}"

    staged_body = stage_body(body, relocs)
    padded_body = staged_body + b"\x00" * (ORIG_SIZE - len(staged_body))

    for idx, (k, idx_v, sv, br) in enumerate(cases):
        recon_res = run_test_case(padded_body, k, idx_v, sv, br)
        orig_res = orig_results[idx]

        assert recon_res["ret"] == orig_res["ret"], (
            f"Case (key={k}, idx={idx_v}, stat={sv}, req={br}): mismatch: recon={recon_res['ret']} vs orig={orig_res['ret']}"
        )
        assert recon_res["r4"] == orig_res["r4"] == 0x44444444
        assert recon_res["r5"] == orig_res["r5"] == 0x55555555
        assert recon_res["r6"] == orig_res["r6"] == 0x66666666
        assert recon_res["r7"] == orig_res["r7"] == 0x77777777
        assert recon_res["r8"] == orig_res["r8"] == 0x88888888

    print(f"PASS: All {len(cases)} cases matched identically!")

    print("Testing negative controls (mutations)...")
    mutant_source = SOURCE.read_text(encoding="utf-8").replace(
        "scale = 100;", "scale = 101;"
    )
    mutant_file = args.out_dir / "mutant_scale.cpp"
    mutant_file.write_text(mutant_source, encoding="utf-8")
    m_body, m_relocs, _, _ = compile_body(args.out_dir, mutant_file)
    m_staged = stage_body(m_body, m_relocs)
    m_padded = m_staged + b"\x00" * (ORIG_SIZE - len(m_staged))
    m_res = run_test_case(m_padded, 1, 1, 10, 15)
    assert m_res["ret"] != orig_results[0]["ret"], "Mutant not detected!"
    print("  Detected mutant: mutant_scale (modified base scale)")

    report = {
        "function": "camp_func_002960d4",
        "address": hex(ORIG_ADDR),
        "slot_size": ORIG_SIZE,
        "compiled_size": len(body),
        "test_cases_count": len(cases),
        "all_cases_passed": True,
        "negative_controls_detected": 1,
    }
    report_path = args.out_dir / "report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"Saved report to {report_path}")


if __name__ == "__main__":
    main()
