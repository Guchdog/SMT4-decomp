#!/usr/bin/env python3
"""Differential test for engine_func_002502e8 (0x002502E8).

Validates that reconstructed C++ matches original ARM binary across all
combinations of quaternion / rotation inputs, checking 4x4 matrix output.
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
    UC_ARM_REG_SP,
    UC_ARM_REG_LR,
    UC_ARM_REG_PC,
    UC_ARM_REG_FPEXC,
)

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k

ORIG_BIN = ROOT / "extracted/exefs/code.bin"
ORIG_ADDR = 0x002502E8
ORIG_SIZE = 128

STACK_BASE = 0x10080000
STACK_SIZE = 0x10000
CODE_BASE = 0x00100000
CODE_SIZE = 0x00380000  # code.bin covers up to 0x480000
DATA_BASE = 0x00480000
DATA_SIZE = 0x00080000  # covers 0x004EA81C and up to 0x00500000

DST_ADDR = 0x10010000
SRC_ADDR = 0x10010100

SOURCE = ROOT / "src/engine/leaf_batch30_c.cpp"

SYMBOL_MAP = {
    "engine_func_00256c3c": 0x00256C3C,
    "func_003f6ea8": 0x003F6EA8,
    "ui_func_002a2f1c": 0x002A2F1C,
}


def load_code_image() -> bytearray:
    with open(ORIG_BIN, "rb") as f:
        data = f.read()
    # Ensure it covers up to CODE_SIZE
    buf = bytearray(CODE_SIZE)
    buf[: len(data)] = data
    return buf


def compile_body(out: Path, source: Path = SOURCE):
    obj = out / "leaf_batch30_c.o"
    result = compile_tu_armv6k(source, obj, ROOT)
    if result.returncode != 0:
        raise RuntimeError(result.stderr or "ARMv6K translation unit compile failed")
    funcs = extract_elf_functions_detailed(obj)
    for sym_name, (body, relocs) in funcs.items():
        if "002502e8" in sym_name:
            return body, relocs, obj, sym_name
    raise KeyError("engine_func_002502e8 not found in compiled object")


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


def run_test_case(code_image: bytes, quat: tuple[float, float, float, float], is_thumb: bool = False):
    uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc.mem_map(CODE_BASE, CODE_SIZE)
    uc.mem_write(CODE_BASE, code_image)

    uc.mem_map(DATA_BASE, DATA_SIZE)
    # Zero data region
    uc.mem_write(DATA_BASE, b"\x00" * 0x1000)

    uc.mem_map(STACK_BASE, STACK_SIZE)
    # Map dst/src scratch memory
    uc.mem_map(0x10000000, 0x20000)

    # Initialize destination with poison pattern
    uc.mem_write(DST_ADDR, b"\xee" * 64)

    # Write input quaternion
    uc.mem_write(SRC_ADDR, struct.pack("<4f", *quat))

    sp = STACK_BASE + 0x8000
    lr = 0x00101234
    uc.mem_write(lr, struct.pack("<I", 0xE1200070))  # bkpt #0

    uc.reg_write(UC_ARM_REG_FPEXC, 0x40000000)
    uc.reg_write(UC_ARM_REG_SP, sp)
    uc.reg_write(UC_ARM_REG_LR, lr)
    uc.reg_write(UC_ARM_REG_R0, DST_ADDR)
    uc.reg_write(UC_ARM_REG_R1, SRC_ADDR)
    uc.reg_write(UC_ARM_REG_R4, 0x44444444)
    uc.reg_write(UC_ARM_REG_R5, 0x55555555)
    uc.reg_write(UC_ARM_REG_R6, 0x66666666)

    try:
        uc.emu_start(ORIG_ADDR | (1 if is_thumb else 0), lr, timeout=5000000)
    except Exception as e:
        pc = uc.reg_read(UC_ARM_REG_PC)
        if pc != lr:
            raise RuntimeError(f"Emulation failed at PC={pc:#x}: {e}")

    dst_bytes = uc.mem_read(DST_ADDR, 64)
    matrix_floats = struct.unpack("<16f", dst_bytes)
    matrix_raw = struct.unpack("<16I", dst_bytes)
    r4 = uc.reg_read(UC_ARM_REG_R4)
    r5 = uc.reg_read(UC_ARM_REG_R5)
    r6 = uc.reg_read(UC_ARM_REG_R6)

    return {
        "matrix_floats": matrix_floats,
        "matrix_raw": matrix_raw,
        "r4": r4,
        "r5": r5,
        "r6": r6,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=ROOT / "build/agent-work/H2-semantic/engine-002502e8/run001")
    args = parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    base_image = load_code_image()

    test_quats = [
        (0.0, 0.0, 0.0, 1.0),       # identity
        (0.70710678, 0.0, 0.0, 0.70710678), # 90 deg X
        (0.0, 0.70710678, 0.0, 0.70710678), # 90 deg Y
        (0.0, 0.0, 0.70710678, 0.70710678), # 90 deg Z
        (0.5, 0.5, 0.5, 0.5),       # 120 deg diag
        (-0.5, 0.5, -0.5, 0.5),
        (0.38268343, 0.0, 0.0, 0.92387953), # 45 deg X
        (0.0, 0.38268343, 0.0, 0.92387953), # 45 deg Y
        (0.0, 0.0, 0.38268343, 0.92387953), # 45 deg Z
        (0.1, 0.2, 0.3, 0.4),       # unnormalized
        (-0.8, -0.2, 0.5, 0.1),
        (1.0, 0.0, 0.0, 0.0),       # 180 deg X
        (0.0, 1.0, 0.0, 0.0),       # 180 deg Y
        (0.0, 0.0, 1.0, 0.0),       # 180 deg Z
    ]

    print(f"Running {len(test_quats)} differential test cases on original binary...")
    orig_results = []
    for q in test_quats:
        res = run_test_case(bytes(base_image), q)
        orig_results.append(res)

    body, relocs, obj, sym_name = compile_body(args.out_dir)
    print(f"Compiled {sym_name}: {len(body)} bytes (slot {ORIG_SIZE} bytes)")
    assert len(body) <= ORIG_SIZE, f"Compiled code size {len(body)} exceeds slot {ORIG_SIZE}"

    staged_body = stage_body(body, relocs)
    padded_body = staged_body + b"\x00" * (ORIG_SIZE - len(staged_body))

    recon_image = bytearray(base_image)
    recon_image[ORIG_ADDR - CODE_BASE : ORIG_ADDR - CODE_BASE + ORIG_SIZE] = padded_body

    print(f"Comparing reconstructed implementation on {len(test_quats)} cases...")
    for idx, q in enumerate(test_quats):
        recon_res = run_test_case(bytes(recon_image), q)
        orig_res = orig_results[idx]

        for elem_idx in range(16):
            assert recon_res["matrix_raw"][elem_idx] == orig_res["matrix_raw"][elem_idx], (
                f"Quat {q} elem {elem_idx}: recon={recon_res['matrix_raw'][elem_idx]:#x} vs orig={orig_res['matrix_raw'][elem_idx]:#x}"
            )
        assert recon_res["r4"] == orig_res["r4"] == 0x44444444
        assert recon_res["r5"] == orig_res["r5"] == 0x55555555
        assert recon_res["r6"] == orig_res["r6"] == 0x66666666

    print(f"PASS: All {len(test_quats)} cases matched identically!")

    print("Testing negative controls (mutations)...")
    mutant_source = SOURCE.read_text(encoding="utf-8").replace(
        "dst[12] = 0.0f;", "dst[12] = 1.0f;"
    )
    mutant_file = args.out_dir / "mutant_dst12.cpp"
    mutant_file.write_text(mutant_source, encoding="utf-8")
    m_body, m_relocs, _, _ = compile_body(args.out_dir, mutant_file)
    m_staged = stage_body(m_body, m_relocs)
    m_padded = m_staged + b"\x00" * (ORIG_SIZE - len(m_staged))
    m_image = bytearray(base_image)
    m_image[ORIG_ADDR - CODE_BASE : ORIG_ADDR - CODE_BASE + ORIG_SIZE] = m_padded
    m_res = run_test_case(bytes(m_image), test_quats[0])
    assert m_res["matrix_raw"][12] != orig_results[0]["matrix_raw"][12], "Mutant not detected!"
    print("  Detected mutant: mutant_dst12 (modified matrix element 12)")

    report = {
        "function": "engine_func_002502e8",
        "address": hex(ORIG_ADDR),
        "slot_size": ORIG_SIZE,
        "compiled_size": len(body),
        "test_cases_count": len(test_quats),
        "all_cases_passed": True,
        "negative_controls_detected": 1,
    }
    report_path = args.out_dir / "report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"Saved report to {report_path}")


if __name__ == "__main__":
    main()
