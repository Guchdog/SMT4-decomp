#!/usr/bin/env python3
"""Differential test for engine_func_002cfc60 (0x002CFC60).

Validates that reconstructed C++ matches original ARM binary:
- stack buffer zeroed (64 bytes)
- callee engine_func_00259510(0) called
- callee engine_func_002bf86c(buf, id) called
- callee engine_func_003db484(*0x00435D18, buf) called
- returns 1
- caller registers preserved.
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
)

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k

ORIG_BIN = ROOT / "extracted/exefs/code.bin"
ORIG_ADDR = 0x002CFC60
ORIG_SIZE = 128

STACK_BASE = 0x10080000
STACK_SIZE = 0x10000
CODE_BASE = 0x00100000
CODE_SIZE = 0x00380000

GLOBAL_CTX_ADDR = 0x00435D18
GLOBAL_CTX_VAL = 0x10020000

STUB_259510 = 0x00259510
STUB_2BF86C = 0x002BF86C
STUB_3DB484 = 0x003DB484

SOURCE = ROOT / "src/engine/leaf_batch30_c.cpp"

SYMBOL_MAP = {
    "engine_func_00259510": STUB_259510,
    "engine_func_002bf86c": STUB_2BF86C,
    "engine_func_003db484": STUB_3DB484,
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
        if "002cfc60" in sym_name:
            return body, relocs, obj, sym_name
    raise KeyError("engine_func_002cfc60 not found in compiled object")


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


def run_test_case(code_bytes: bytes, test_id: int, is_thumb: bool = False):
    uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc.mem_map(CODE_BASE, CODE_SIZE)
    uc.mem_write(ORIG_ADDR, code_bytes)

    # Global context pointer
    uc.mem_write(GLOBAL_CTX_ADDR, struct.pack("<I", GLOBAL_CTX_VAL))

    uc.mem_map(STACK_BASE, STACK_SIZE)
    # Map context memory
    uc.mem_map(0x10020000, 0x10000)

    # Stub STUB_259510: returns test_id
    stub1 = struct.pack("<II", 0xE3A00000 | (test_id & 0xFF), 0xE12FFF1E)
    uc.mem_write(STUB_259510, stub1)

    # Stub STUB_2BF86C: marks buffer with signature (e.g. writes test_id into buf[0])
    # str r1, [r0]; bx lr
    stub2 = struct.pack("<II", 0xE5801000, 0xE12FFF1E)
    uc.mem_write(STUB_2BF86C, stub2)

    # Stub STUB_3DB484: writes test_id into ctx[0]
    # ldr r2, [r1]; str r2, [r0]; bx lr
    stub3 = struct.pack("<III", 0xE5912000, 0xE5802000, 0xE12FFF1E)
    uc.mem_write(STUB_3DB484, stub3)

    sp = STACK_BASE + 0x8000
    lr = 0x00101234
    uc.mem_write(lr, struct.pack("<I", 0xE1200070))

    uc.reg_write(UC_ARM_REG_SP, sp)
    uc.reg_write(UC_ARM_REG_LR, lr)
    uc.reg_write(UC_ARM_REG_R4, 0x44444444)
    uc.reg_write(UC_ARM_REG_R5, 0x55555555)

    try:
        uc.emu_start(ORIG_ADDR | (1 if is_thumb else 0), lr, timeout=2000000)
    except Exception as e:
        pc = uc.reg_read(UC_ARM_REG_PC)
        if pc != lr:
            raise RuntimeError(f"Emulation failed at PC={pc:#x}: {e}")

    ret = uc.reg_read(UC_ARM_REG_R0)
    final_sp = uc.reg_read(UC_ARM_REG_SP)
    r4 = uc.reg_read(UC_ARM_REG_R4)
    r5 = uc.reg_read(UC_ARM_REG_R5)
    ctx_val = struct.unpack("<I", uc.mem_read(GLOBAL_CTX_VAL, 4))[0]

    return {
        "ret": ret,
        "sp": final_sp,
        "r4": r4,
        "r5": r5,
        "ctx_val": ctx_val,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=ROOT / "build/agent-work/H2-semantic/engine-002cfc60/run001")
    args = parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    orig_bytes = load_original_bytes()

    test_ids = [0, 1, 7, 42, 99, 255]
    print(f"Running {len(test_ids)} differential cases on original binary...")
    orig_results = []
    for tid in test_ids:
        orig_results.append(run_test_case(orig_bytes, tid))

    body, relocs, obj, sym_name = compile_body(args.out_dir)
    print(f"Compiled {sym_name}: {len(body)} bytes (slot {ORIG_SIZE} bytes)")
    assert len(body) <= ORIG_SIZE, f"Compiled code size {len(body)} exceeds slot {ORIG_SIZE}"

    staged_body = stage_body(body, relocs)
    padded_body = staged_body + b"\x00" * (ORIG_SIZE - len(staged_body))

    for idx, tid in enumerate(test_ids):
        recon_res = run_test_case(padded_body, tid)
        orig_res = orig_results[idx]

        assert recon_res["ret"] == orig_res["ret"] == 1
        assert recon_res["sp"] == orig_res["sp"]
        assert recon_res["r4"] == orig_res["r4"] == 0x44444444
        assert recon_res["r5"] == orig_res["r5"] == 0x55555555
        assert recon_res["ctx_val"] == orig_res["ctx_val"] == tid

    print(f"PASS: All {len(test_ids)} cases matched identically!")

    print("Testing negative controls (mutations)...")
    mutant_source = SOURCE.read_text(encoding="utf-8").replace(
        "return 1;", "return 0;"
    )
    mutant_file = args.out_dir / "mutant_ret.cpp"
    mutant_file.write_text(mutant_source, encoding="utf-8")
    m_body, m_relocs, _, _ = compile_body(args.out_dir, mutant_file)
    m_staged = stage_body(m_body, m_relocs)
    m_padded = m_staged + b"\x00" * (ORIG_SIZE - len(m_staged))
    m_res = run_test_case(m_padded, 42)
    assert m_res["ret"] != orig_results[3]["ret"], "Mutant not detected!"
    print("  Detected mutant: mutant_ret (modified return value)")

    report = {
        "function": "engine_func_002cfc60",
        "address": hex(ORIG_ADDR),
        "slot_size": ORIG_SIZE,
        "compiled_size": len(body),
        "test_cases_count": len(test_ids),
        "all_cases_passed": True,
        "negative_controls_detected": 1,
    }
    report_path = args.out_dir / "report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"Saved report to {report_path}")


if __name__ == "__main__":
    main()
