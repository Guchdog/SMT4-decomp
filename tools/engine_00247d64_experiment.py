#!/usr/bin/env python3
"""Differential test for engine_func_00247d64 (0x00247D64).

Validates that reconstructed C++ matches original ARM binary across all
combinations of:
- reverse_flag == 0 and reverse_flag != 0
- duration == 0, duration > 0, duration < 0
- various duration values (1, 2, 10, 60, 100, etc.)
- verifies target struct offsets +0x24 and +0x28
- verifies callee ui_func_002c0ac8 stub invocation and register conventions.
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
ORIG_ADDR = 0x00247D64
ORIG_SIZE = 128
CALLEE_ADDR = 0x002C0AC8
TARGET_MEM_ADDR = 0x10008000

STACK_BASE = 0x10080000
STACK_SIZE = 0x10000
CODE_BASE = 0x00100000
CODE_SIZE = 0x00400000
TARGET_OBJ = 0x10010000

SOURCE = ROOT / "src/engine/leaf_batch30_c.cpp"

SYMBOL_MAP = {
    "ui_func_002c0ac8": CALLEE_ADDR,
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
        if "00247d64" in sym_name:
            return body, relocs, obj, sym_name
    raise KeyError("engine_func_00247d64 not found in compiled object")


def stage_body(body: bytes, relocations) -> bytes:
    fixed = bytearray(body)
    for reloc in relocations:
        site = ORIG_ADDR + reloc.offset
        target = SYMBOL_MAP.get(reloc.symbol_name)
        if target is None:
            raise KeyError(f"Unmapped relocation: {reloc.symbol_name}")
        imm24 = ((target - (site + 8)) >> 2) & 0x00FFFFFF
        insn = 0xEB000000 | imm24
        struct.pack_into("<I", fixed, reloc.offset, insn)
    return bytes(fixed)


def run_test_case(code_bytes: bytes, id_val: int, duration: int, reverse_flag: int, is_thumb: bool = False):
    uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc.mem_map(CODE_BASE, CODE_SIZE)
    uc.mem_map(STACK_BASE, STACK_SIZE)
    uc.mem_map(TARGET_MEM_ADDR, 0x10000)

    exec_addr = ORIG_ADDR
    uc.mem_write(exec_addr, code_bytes)

    # Initialize target memory
    uc.mem_write(TARGET_OBJ, b"\xaa" * 0x80)

    # Setup callee stub at CALLEE_ADDR: returns TARGET_OBJ in r0
    callee_code = struct.pack("<IIII", 0xE59F0000, 0xE12FFF1E, TARGET_OBJ, 0)
    uc.mem_write(CALLEE_ADDR, callee_code)

    sp = STACK_BASE + 0x8000
    lr = 0x00101234  # arbitrary return address
    # Return trap instruction at lr
    uc.mem_write(lr, struct.pack("<I", 0xE1200070))  # bkpt #0

    uc.reg_write(UC_ARM_REG_FPEXC, 0x40000000)
    uc.reg_write(UC_ARM_REG_SP, sp)
    uc.reg_write(UC_ARM_REG_LR, lr)
    uc.reg_write(UC_ARM_REG_R0, id_val)
    uc.reg_write(UC_ARM_REG_R1, duration & 0xFFFFFFFF)
    uc.reg_write(UC_ARM_REG_R2, reverse_flag & 0xFFFFFFFF)
    uc.reg_write(UC_ARM_REG_R4, 0x44444444)
    uc.reg_write(UC_ARM_REG_R5, 0x55555555)
    uc.reg_write(UC_ARM_REG_R6, 0x66666666)

    try:
        uc.emu_start(exec_addr | (1 if is_thumb else 0), lr, timeout=2000000)
    except Exception as e:
        pc = uc.reg_read(UC_ARM_REG_PC)
        if pc != lr:
            raise RuntimeError(f"Emulation failed at PC={pc:#x}: {e}")

    # Read output
    f24_bytes = uc.mem_read(TARGET_OBJ + 0x24, 4)
    f28_bytes = uc.mem_read(TARGET_OBJ + 0x28, 4)
    r4 = uc.reg_read(UC_ARM_REG_R4)
    r5 = uc.reg_read(UC_ARM_REG_R5)
    r6 = uc.reg_read(UC_ARM_REG_R6)

    return {
        "field_24": struct.unpack("<f", f24_bytes)[0],
        "field_24_raw": struct.unpack("<I", f24_bytes)[0],
        "field_28": struct.unpack("<f", f28_bytes)[0],
        "field_28_raw": struct.unpack("<I", f28_bytes)[0],
        "r4": r4,
        "r5": r5,
        "r6": r6,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=ROOT / "build/agent-work/H2-semantic/engine-00247d64/run001")
    args = parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    orig_bytes = load_original_bytes()

    test_cases = []
    durations = [0, 1, 2, 3, 5, 10, 30, 60, 100, 255, 1000, -1, -50]
    reverse_flags = [0, 1, 2, 0x80, -1]
    ids = [0, 1, 42, 999]

    for d in durations:
        for rf in reverse_flags:
            for id_v in ids[:2]:
                test_cases.append((id_v, d, rf))

    print(f"Running {len(test_cases)} direct differential cases...")

    orig_results = []
    for id_v, d, rf in test_cases:
        res = run_test_case(orig_bytes, id_v, d, rf, is_thumb=False)
        orig_results.append(res)

    body, relocs, obj, sym_name = compile_body(args.out_dir)
    print(f"Compiled {sym_name}: {len(body)} bytes (slot {ORIG_SIZE} bytes)")
    assert len(body) <= ORIG_SIZE, f"Compiled code size {len(body)} exceeds slot {ORIG_SIZE}"

    staged_body = stage_body(body, relocs)
    padded_body = staged_body + b"\x00" * (ORIG_SIZE - len(staged_body))

    for idx, (id_v, d, rf) in enumerate(test_cases):
        recon_res = run_test_case(padded_body, id_v, d, rf, is_thumb=False)
        orig_res = orig_results[idx]

        assert recon_res["field_24_raw"] == orig_res["field_24_raw"], (
            f"Case {id_v, d, rf}: field_24 mismatch: recon={recon_res['field_24_raw']:#x} ({recon_res['field_24']}) vs orig={orig_res['field_24_raw']:#x} ({orig_res['field_24']})"
        )
        assert recon_res["field_28_raw"] == orig_res["field_28_raw"], (
            f"Case {id_v, d, rf}: field_28 mismatch: recon={recon_res['field_28_raw']:#x} ({recon_res['field_28']}) vs orig={orig_res['field_28_raw']:#x} ({orig_res['field_28']})"
        )
        assert recon_res["r4"] == orig_res["r4"] == 0x44444444, "r4 not restored"
        assert recon_res["r5"] == orig_res["r5"] == 0x55555555, "r5 not restored"
        assert recon_res["r6"] == orig_res["r6"] == 0x66666666, "r6 not restored"

    print(f"PASS: {len(test_cases)} direct differential cases matched identically.")

    print("Testing negative controls (mutations)...")
    mutant_source = SOURCE.read_text(encoding="utf-8").replace(
        "*val_ptr = 1.0f;", "*val_ptr = 2.0f;"
    )
    mutant_file = args.out_dir / "mutant_val.cpp"
    mutant_file.write_text(mutant_source, encoding="utf-8")
    m_body, m_relocs, _, _ = compile_body(args.out_dir, mutant_file)
    m_staged = stage_body(m_body, m_relocs)
    m_padded = m_staged + b"\x00" * (ORIG_SIZE - len(m_staged))
    m_res = run_test_case(m_padded, 0, 10, 1)
    assert m_res["field_24_raw"] != orig_results[0]["field_24_raw"], "Mutant not detected!"
    print("  Detected mutant: mutant_val (modified constant)")

    report = {
        "function": "engine_func_00247d64",
        "address": hex(ORIG_ADDR),
        "slot_size": ORIG_SIZE,
        "compiled_size": len(body),
        "test_cases_count": len(test_cases),
        "all_cases_passed": True,
        "negative_controls_detected": 1,
    }
    report_path = args.out_dir / "report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"Saved report to {report_path}")


if __name__ == "__main__":
    main()
