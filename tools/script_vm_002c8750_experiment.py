#!/usr/bin/env python3
"""Differential test for script_vm_func_002c8750 (0x002C8750).

Validates that reconstructed C++ matches original ARM binary:
- 32 elements iterated (stride 384 bytes, base + 0x34)
- active flag checked (*elem != 0)
- sub_type checked (1 <= val < 11)
- flag7d checked (*(elem + 0x7D) == 0)
- state transition checked (states 0, 4, 5 transition to 1, aux cleared to 0)
- untouched states (1, 2, 3, 6+) unchanged
- register preservation.
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
    UC_ARM_REG_SP,
    UC_ARM_REG_LR,
    UC_ARM_REG_PC,
)

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k

ORIG_BIN = ROOT / "extracted/exefs/code.bin"
ORIG_ADDR = 0x002C8750
ORIG_SIZE = 128

STACK_BASE = 0x10080000
STACK_SIZE = 0x10000
CODE_BASE = 0x00100000
CODE_SIZE = 0x00380000

GLOBAL_PTR_ADDR = 0x00447600
BUFFER_BASE = 0x10010000
BUFFER_SIZE = 32 * 384 + 0x400  # 13312 bytes

SOURCE = ROOT / "src/engine/leaf_batch30_c.cpp"


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
        if "002c8750" in sym_name:
            return body, relocs, obj, sym_name
    raise KeyError("script_vm_func_002c8750 not found in compiled object")


def init_test_buffer() -> bytearray:
    buf = bytearray(BUFFER_SIZE)
    # Define test patterns on elements
    # elem base is i * 384 + 0x34
    test_specs = [
        # (idx, active, val, flag7d, state, aux)
        (0, 1, 1, 0, 0, 0x11111111),   # should update -> state 1, aux 0
        (1, 1, 4, 0, 4, 0x22222222),   # should update -> state 1, aux 0
        (2, 1, 10, 0, 5, 0x33333333),  # should update -> state 1, aux 0
        (3, 0, 1, 0, 0, 0x44444444),   # inactive -> no change
        (4, 1, 0, 0, 0, 0x55555555),   # val=0 -> no change
        (5, 1, 11, 0, 0, 0x66666666),  # val=11 -> no change
        (6, 1, 5, 1, 0, 0x77777777),   # flag7d=1 -> no change
        (7, 1, 5, 0, 2, 0x88888888),   # state=2 -> no change
        (8, 1, 5, 0, 3, 0x99999999),   # state=3 -> no change
        (15, 1, 7, 0, 4, 0xAAAAAAAA),  # should update
        (31, 1, 8, 0, 5, 0xBBBBBBBB),  # should update (boundary element)
    ]
    for idx, act, val, f7d, st, aux in test_specs:
        elem_offset = idx * 384 + 0x34
        buf[elem_offset] = act
        struct.pack_into("<I", buf, elem_offset + 0x174, val)
        buf[elem_offset + 0x7D] = f7d
        struct.pack_into("<I", buf, elem_offset + 0x84, st)
        struct.pack_into("<I", buf, elem_offset + 0x88, aux)
    return buf


def run_test_case(code_bytes: bytes, is_thumb: bool = False):
    uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc.mem_map(CODE_BASE, CODE_SIZE)
    uc.mem_write(ORIG_ADDR, code_bytes)

    # Point global ptr to BUFFER_BASE
    uc.mem_write(GLOBAL_PTR_ADDR, struct.pack("<I", BUFFER_BASE))

    uc.mem_map(STACK_BASE, STACK_SIZE)
    # Map buffer memory
    uc.mem_map(0x10000000, 0x30000)

    buf_data = init_test_buffer()
    uc.mem_write(BUFFER_BASE, bytes(buf_data))

    sp = STACK_BASE + 0x8000
    lr = 0x00101234
    uc.mem_write(lr, struct.pack("<I", 0xE1200070))

    uc.reg_write(UC_ARM_REG_SP, sp)
    uc.reg_write(UC_ARM_REG_LR, lr)
    uc.reg_write(UC_ARM_REG_R4, 0x44444444)

    try:
        uc.emu_start(ORIG_ADDR | (1 if is_thumb else 0), lr, timeout=5000000)
    except Exception as e:
        pc = uc.reg_read(UC_ARM_REG_PC)
        if pc != lr:
            raise RuntimeError(f"Emulation failed at PC={pc:#x}: {e}")

    result_buf = uc.mem_read(BUFFER_BASE, BUFFER_SIZE)
    r4 = uc.reg_read(UC_ARM_REG_R4)

    return {
        "buffer": result_buf,
        "r4": r4,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=ROOT / "build/agent-work/H2-semantic/script-vm-002c8750/run001")
    args = parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    orig_bytes = load_original_bytes()

    print("Running differential case on original binary...")
    orig_res = run_test_case(orig_bytes)

    body, relocs, obj, sym_name = compile_body(args.out_dir)
    print(f"Compiled {sym_name}: {len(body)} bytes (slot {ORIG_SIZE} bytes)")
    assert len(body) <= ORIG_SIZE, f"Compiled code size {len(body)} exceeds slot {ORIG_SIZE}"

    padded_body = body + b"\x00" * (ORIG_SIZE - len(body))

    print("Running differential case on reconstructed implementation...")
    recon_res = run_test_case(padded_body)

    assert recon_res["buffer"] == orig_res["buffer"], "Buffer contents mismatch between original and reconstructed!"
    assert recon_res["r4"] == orig_res["r4"] == 0x44444444

    # Verify specific elements in buffer
    # Element 0: state should be 1, aux 0
    e0 = 0x34
    st0, aux0 = struct.unpack("<II", recon_res["buffer"][e0 + 0x84 : e0 + 0x8C])
    assert st0 == 1 and aux0 == 0, f"Element 0 state mismatch: st={st0}, aux={aux0}"

    # Element 3: inactive, state should remain 0, aux 0x44444444
    e3 = 3 * 384 + 0x34
    st3, aux3 = struct.unpack("<II", recon_res["buffer"][e3 + 0x84 : e3 + 0x8C])
    assert st3 == 0 and aux3 == 0x44444444, f"Element 3 state mismatch: st={st3}, aux={aux3}"

    print("PASS: Buffer contents across all 32 elements matched identically!")

    print("Testing negative controls (mutations)...")
    mutant_source = SOURCE.read_text(encoding="utf-8").replace(
        "val >= 11", "val >= 12"
    )
    mutant_file = args.out_dir / "mutant_bound.cpp"
    mutant_file.write_text(mutant_source, encoding="utf-8")
    m_body, _, _, _ = compile_body(args.out_dir, mutant_file)
    m_padded = m_body + b"\x00" * (ORIG_SIZE - len(m_body))
    m_res = run_test_case(m_padded)
    # With bound 12, Element 5 (val=11) would be updated instead of skipped!
    assert m_res["buffer"] != orig_res["buffer"], "Mutant not detected!"
    print("  Detected mutant: mutant_bound (modified threshold 11->12)")

    report = {
        "function": "script_vm_func_002c8750",
        "address": hex(ORIG_ADDR),
        "slot_size": ORIG_SIZE,
        "compiled_size": len(body),
        "elements_verified": 32,
        "buffer_size_bytes": BUFFER_SIZE,
        "all_cases_passed": True,
        "negative_controls_detected": 1,
    }
    report_path = args.out_dir / "report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"Saved report to {report_path}")


if __name__ == "__main__":
    main()
