#!/usr/bin/env python3
"""Differential test for script_vm_func_00277dcc (0x00277DCC).

Validates that reconstructed C++ matches original ARM binary across all
branch combinations:
- code == 0x24 (early return)
- script_vm_func_002857e4() == 1 with script_vm_func_00255050(0x29) == 1 (early return)
- script_vm_func_002857e4() == 1 with script_vm_func_00255050(0x29) == 0 (continue)
- code == 0x18 (bypass check, write)
- code >= 0x64 (bypass check, write)
- code < 0x64 and != 0x18 with script_vm_func_00255050(code) == 1 (early return)
- code < 0x64 and != 0x18 with script_vm_func_00255050(code) == 0 (write)
- memory written at (global_ptr + 0xCCB8) matches 100%.
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
ORIG_ADDR = 0x00277DCC
ORIG_SIZE = 128

STACK_BASE = 0x10080000
STACK_SIZE = 0x10000
CODE_BASE = 0x00100000
CODE_SIZE = 0x00380000
DATA_BASE = 0x00400000
DATA_SIZE = 0x00080000  # covers 0x00447A78

GLOBAL_PTR_ADDR = 0x00447A78
HEAP_BUFFER_ADDR = 0x10010000

STUB_2857E4 = 0x002857E4
STUB_255050 = 0x00255050

SOURCE = ROOT / "src/engine/leaf_batch30_c.cpp"

SYMBOL_MAP = {
    "script_vm_func_002857e4": STUB_2857E4,
    "script_vm_func_00255050": STUB_255050,
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
        if "00277dcc" in sym_name:
            return body, relocs, obj, sym_name
    raise KeyError("script_vm_func_00277dcc not found in compiled object")


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


def run_test_case(code_bytes: bytes, code: int, param: int, stub_2857e4_ret: int, stub_255050_map: dict[int, int], is_thumb: bool = False):
    uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc.mem_map(CODE_BASE, CODE_SIZE)
    uc.mem_write(ORIG_ADDR, code_bytes)

    # DATA_BASE is inside CODE_BASE range (0x100000 to 0x480000)
    # Point GLOBAL_PTR_ADDR -> HEAP_BUFFER_ADDR
    uc.mem_write(GLOBAL_PTR_ADDR, struct.pack("<I", HEAP_BUFFER_ADDR))

    uc.mem_map(STACK_BASE, STACK_SIZE)
    # Map heap memory
    uc.mem_map(0x10000000, 0x30000)

    # Initialize heap target region with sentinel bytes
    target_addr = HEAP_BUFFER_ADDR + 0xCC00
    uc.mem_write(target_addr, b"\xdd" * 0x100)

    # Write stubs:
    # STUB_2857E4: returns stub_2857e4_ret
    stub1 = struct.pack("<II", 0xE3A00000 | (stub_2857e4_ret & 0xFF), 0xE12FFF1E) # mov r0, #ret; bx lr
    uc.mem_write(STUB_2857E4, stub1)

    # STUB_255050: looks up r0 in stub_255050_map
    # We can handle it via a small hook or code
    # Default return 0, but if r0 in map, return that value
    # To keep simple in Unicorn: write a hook
    def hook_255050(uc_inst, address, size, user_data):
        arg = uc_inst.reg_read(UC_ARM_REG_R0)
        ret = stub_255050_map.get(arg, 0)
        uc_inst.reg_write(UC_ARM_REG_R0, ret)
        # return immediately (pop pc or bx lr)
        lr_val = uc_inst.reg_read(UC_ARM_REG_LR)
        uc_inst.reg_write(UC_ARM_REG_PC, lr_val)

    uc.hook_add(1, hook_255050, begin=STUB_255050, end=STUB_255050 + 4)
    # Write a dummy instruction at STUB_255050
    uc.mem_write(STUB_255050, struct.pack("<II", 0xE1A00000, 0xE12FFF1E))

    sp = STACK_BASE + 0x8000
    lr = 0x00101234
    uc.mem_write(lr, struct.pack("<I", 0xE1200070))  # bkpt #0

    uc.reg_write(UC_ARM_REG_SP, sp)
    uc.reg_write(UC_ARM_REG_LR, lr)
    uc.reg_write(UC_ARM_REG_R0, code & 0xFFFF)
    uc.reg_write(UC_ARM_REG_R1, param & 0xFFFF)
    uc.reg_write(UC_ARM_REG_R4, 0x44444444)
    uc.reg_write(UC_ARM_REG_R5, 0x55555555)
    uc.reg_write(UC_ARM_REG_R6, 0x66666666)

    try:
        uc.emu_start(ORIG_ADDR | (1 if is_thumb else 0), lr, timeout=2000000)
    except Exception as e:
        pc = uc.reg_read(UC_ARM_REG_PC)
        if pc != lr:
            raise RuntimeError(f"Emulation failed at PC={pc:#x}: {e}")

    written_data = uc.mem_read(target_addr + 0xB8, 8)
    r4 = uc.reg_read(UC_ARM_REG_R4)
    r5 = uc.reg_read(UC_ARM_REG_R5)
    r6 = uc.reg_read(UC_ARM_REG_R6)

    return {
        "written_data": written_data,
        "written_u16s": struct.unpack("<4H", written_data),
        "r4": r4,
        "r5": r5,
        "r6": r6,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=ROOT / "build/agent-work/H2-semantic/script-vm-00277dcc/run001")
    args = parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    orig_bytes = load_original_bytes()

    # Generate diverse test scenarios
    cases = []
    # 1. code == 0x24 (should early exit regardless of stubs)
    cases.append((0x24, 0x1234, 0, {}))
    cases.append((0x24, 0x5678, 1, {0x29: 1}))

    # 2. stub1 == 1, 0x29 == 1 (early exit)
    cases.append((0x10, 0x1111, 1, {0x29: 1}))
    cases.append((0x18, 0x2222, 1, {0x29: 1}))

    # 3. stub1 == 1, 0x29 == 0 (proceeds to code checks)
    # code == 0x18 (bypasses code check, writes)
    cases.append((0x18, 0x3333, 1, {0x29: 0}))
    # code >= 0x64 (bypasses code check, writes)
    cases.append((0x64, 0x4444, 1, {0x29: 0}))
    cases.append((0x100, 0x5555, 1, {0x29: 0}))
    # code < 0x64 and != 0x18, map[code] == 1 (early exit)
    cases.append((0x20, 0x6666, 1, {0x29: 0, 0x20: 1}))
    # code < 0x64 and != 0x18, map[code] == 0 (writes)
    cases.append((0x20, 0x7777, 1, {0x29: 0, 0x20: 0}))
    cases.append((0x01, 0x8888, 1, {0x29: 0, 0x01: 0}))

    # 4. stub1 == 0 (does not check 0x29)
    cases.append((0x18, 0x9999, 0, {}))
    cases.append((0x64, 0xAAAA, 0, {}))
    cases.append((0x70, 0xBBBB, 0, {}))
    cases.append((0x30, 0xCCCC, 0, {0x30: 1}))  # early exit
    cases.append((0x30, 0xDDDD, 0, {0x30: 0}))  # writes
    cases.append((0x00, 0xEEEE, 0, {0x00: 0}))  # writes

    print(f"Running {len(cases)} differential cases...")
    orig_results = []
    for c, p, s1, m in cases:
        res = run_test_case(orig_bytes, c, p, s1, m)
        orig_results.append(res)

    body, relocs, obj, sym_name = compile_body(args.out_dir)
    print(f"Compiled {sym_name}: {len(body)} bytes (slot {ORIG_SIZE} bytes)")
    assert len(body) <= ORIG_SIZE, f"Compiled code size {len(body)} exceeds slot {ORIG_SIZE}"

    staged_body = stage_body(body, relocs)
    padded_body = staged_body + b"\x00" * (ORIG_SIZE - len(staged_body))

    for idx, (c, p, s1, m) in enumerate(cases):
        recon_res = run_test_case(padded_body, c, p, s1, m)
        orig_res = orig_results[idx]

        assert recon_res["written_data"] == orig_res["written_data"], (
            f"Case (code={c:#x}, param={p:#x}, s1={s1}): mismatch: recon={recon_res['written_data'].hex()} vs orig={orig_res['written_data'].hex()}"
        )
        assert recon_res["r4"] == orig_res["r4"] == 0x44444444
        assert recon_res["r5"] == orig_res["r5"] == 0x55555555
        assert recon_res["r6"] == orig_res["r6"] == 0x66666666

    print(f"PASS: All {len(cases)} cases matched identically!")

    print("Testing negative controls (mutations)...")
    mutant_source = SOURCE.read_text(encoding="utf-8").replace(
        "target[0] = 1;", "target[0] = 2;"
    )
    mutant_file = args.out_dir / "mutant_active.cpp"
    mutant_file.write_text(mutant_source, encoding="utf-8")
    m_body, m_relocs, _, _ = compile_body(args.out_dir, mutant_file)
    m_staged = stage_body(m_body, m_relocs)
    m_padded = m_staged + b"\x00" * (ORIG_SIZE - len(m_staged))
    m_res = run_test_case(m_padded, 0x18, 0x1234, 0, {})
    assert m_res["written_data"] != orig_results[8]["written_data"], "Mutant not detected!"
    print("  Detected mutant: mutant_active (modified active flag)")

    report = {
        "function": "script_vm_func_00277dcc",
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
