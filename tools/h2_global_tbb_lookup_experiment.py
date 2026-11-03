#!/usr/bin/env python3
"""Final-VMA differential and H2 caller composition for Tbb_GetGlobalSubTable (0x002C0EC4)."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import struct
import sys
from dataclasses import dataclass
from pathlib import Path

import unicorn
from unicorn import arm_const as arm

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k

IMAGE = ROOT / "extracted/exefs/code.bin"
IMAGE_SHA = "1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558"
SOURCE = ROOT / "src/ui/tbb_loader.cpp"
ENTRY, SLOT = 0x002C0EC4, 28
CODE_BASE, CODE_SIZE = 0x00100000, 0x00380000
DATA_BASE, DATA_SIZE = 0x00490000, 0x00020000  # covers 0x0049382C
TBCR_BASE, TBCR_SIZE = 0x00500000, 0x00020000
STACK, STACK_SIZE = 0x08000000, 0x00010000
SP, STOP = STACK + 0x8000, STACK + 0x9000
U32 = 0xFFFFFFFF

GLOBAL_SLOTS_ADDR = 0x0049382C
SUBTABLE_TARGET = 0x002AC2F4  # Tbb_GetSubTable

TBCR_MAGIC = 0x52434254  # 'TBCR'
TBL1_MAGIC = 0x314C4254  # 'TBL1'


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def compile_body(out: Path, source: Path = SOURCE):
    out.mkdir(parents=True, exist_ok=True)
    obj = out / source.name.replace(".cpp", ".o")
    result = compile_tu_armv6k(source, obj, ROOT)
    if result.returncode != 0:
        raise RuntimeError(result.stderr or "ARMv6K translation unit compile failed")
    funcs = extract_elf_functions_detailed(obj)
    # Target function symbol name in C++
    func_key = None
    for k in funcs:
        if "Tbb_GetGlobalSubTable" in k or "002c0ec4" in k:
            func_key = k
            break
    if not func_key:
        raise KeyError("Tbb_GetGlobalSubTable not found in compiled object")
    body, relocations = funcs[func_key]
    if len(body) > SLOT or len(body) % 4 != 0:
        raise ValueError(f"function body does not fit its slot: {len(body)}/{SLOT}")
    return body, relocations, list(result.args), obj


def stage_body(body: bytes, relocations) -> bytes:
    fixed = bytearray(body)
    for reloc in relocations:
        site = ENTRY + reloc.offset
        target = SUBTABLE_TARGET
        delta = target - (site + 8)
        if target & 1 or delta & 3 or not -(1 << 25) <= delta < (1 << 25):
            raise ValueError(f"invalid ARM call target: {reloc}")
        # B instruction opcode: 0xEA000000 | (delta >> 2 & 0x00FFFFFF)
        imm24 = (delta >> 2) & 0x00FFFFFF
        insn = 0xEA000000 | imm24
        struct.pack_into("<I", fixed, reloc.offset, insn)
    return bytes(fixed)


def make_ips(offset: int, data: bytes) -> bytes:
    return b"PATCH" + struct.pack(">BH", (offset >> 16) & 0xFF, offset & 0xFFFF) + struct.pack(">H", len(data)) + data + b"EOF"


def apply_ips(base: bytes, ips: bytes) -> bytes:
    if not ips.startswith(b"PATCH") or not ips.endswith(b"EOF"):
        raise ValueError("malformed IPS")
    out = bytearray(base)
    idx = 5
    while idx < len(ips) - 3:
        offset = (ips[idx] << 16) | (ips[idx + 1] << 8) | ips[idx + 2]
        size = (ips[idx + 3] << 8) | ips[idx + 4]
        idx += 5
        out[offset:offset + size] = ips[idx:idx + size]
        idx += size
    return bytes(out)


def build_tbcr(table_count: int, tbl1_addrs: list[int]) -> bytes:
    # TbcrHeader: u32 magic, u32 file_size, u32 table_count, u32 reserved
    header = struct.pack("<IIII", TBCR_MAGIC, 0x10 + table_count * 4, table_count, 0)
    offsets = bytearray()
    for addr in tbl1_addrs:
        # relative offset from container start
        offsets += struct.pack("<I", addr)
    return header + bytes(offsets)


def run_test(code_image: bytes, slot_id: int, table_index: int, slot_container: int, tbcr_bytes: bytes | None = None) -> dict:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.mem_map(CODE_BASE, CODE_SIZE)
    uc.mem_write(CODE_BASE, code_image)

    uc.mem_map(DATA_BASE, DATA_SIZE)
    # Initialize global slots with zeros
    uc.mem_write(DATA_BASE, bytes(DATA_SIZE))
    # Always write slot_container at the entry address if within DATA_SIZE
    entry_addr = GLOBAL_SLOTS_ADDR + slot_id * 16
    if entry_addr + 8 <= DATA_BASE + DATA_SIZE:
        uc.mem_write(entry_addr + 4, struct.pack("<I", slot_container))

    uc.mem_map(TBCR_BASE, TBCR_SIZE)
    if tbcr_bytes:
        uc.mem_write(TBCR_BASE, tbcr_bytes)

    uc.mem_map(STACK, STACK_SIZE)
    uc.reg_write(arm.UC_ARM_REG_SP, SP)
    uc.reg_write(arm.UC_ARM_REG_LR, STOP)

    # Set non-argument registers to known values
    for r, v in [
        (arm.UC_ARM_REG_R4, 0x44444444),
        (arm.UC_ARM_REG_R5, 0x55555555),
        (arm.UC_ARM_REG_R6, 0x66666666),
        (arm.UC_ARM_REG_R7, 0x77777777),
        (arm.UC_ARM_REG_R8, 0x88888888),
        (arm.UC_ARM_REG_R9, 0x99999999),
        (arm.UC_ARM_REG_R10, 0xAAAAAAAA),
        (arm.UC_ARM_REG_R11, 0xBBBBBBBB),
    ]:
        uc.reg_write(r, v)

    uc.reg_write(arm.UC_ARM_REG_R0, slot_id)
    uc.reg_write(arm.UC_ARM_REG_R1, table_index)
    uc.reg_write(arm.UC_ARM_REG_R2, 0x22222222)
    uc.reg_write(arm.UC_ARM_REG_R3, 0x33333333)

    call_events = []
    mem_writes = []

    def hook_code(emu, address, size, user_data):
        if address == SUBTABLE_TARGET:
            r0 = emu.reg_read(arm.UC_ARM_REG_R0)
            r1 = emu.reg_read(arm.UC_ARM_REG_R1)
            call_events.append(("Tbb_GetSubTable", r0, r1))
        elif address == STOP:
            emu.emu_stop()

    def hook_write(emu, access, address, size, value, user_data):
        mem_writes.append((address, size, value))

    uc.hook_add(unicorn.UC_HOOK_CODE, hook_code)
    uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, hook_write)

    uc.emu_start(ENTRY, STOP, timeout=500000)

    return {
        "r0": uc.reg_read(arm.UC_ARM_REG_R0),
        "r4": uc.reg_read(arm.UC_ARM_REG_R4),
        "r5": uc.reg_read(arm.UC_ARM_REG_R5),
        "r6": uc.reg_read(arm.UC_ARM_REG_R6),
        "r7": uc.reg_read(arm.UC_ARM_REG_R7),
        "r8": uc.reg_read(arm.UC_ARM_REG_R8),
        "r9": uc.reg_read(arm.UC_ARM_REG_R9),
        "r10": uc.reg_read(arm.UC_ARM_REG_R10),
        "r11": uc.reg_read(arm.UC_ARM_REG_R11),
        "sp": uc.reg_read(arm.UC_ARM_REG_SP),
        "call_events": call_events,
        "mem_writes": mem_writes,
    }


def run_caller_test(code_image: bytes, index: int) -> dict:
    """Compose through camp_func_002aea28 (0x002AEA28), which calls Tbb_GetGlobalSubTable(14, 0)."""
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.mem_map(CODE_BASE, CODE_SIZE)
    uc.mem_write(CODE_BASE, code_image)

    uc.mem_map(DATA_BASE, DATA_SIZE)
    uc.mem_write(DATA_BASE, bytes(DATA_SIZE))

    # Slot 14 setup: container at TBCR_BASE
    uc.mem_write(GLOBAL_SLOTS_ADDR + 14 * 16 + 4, struct.pack("<I", TBCR_BASE))

    # TBCR at TBCR_BASE with 1 subtable (index 0) pointing to relative offset 0x20
    # At offset 0x20: TBL1Header: magic='TBL1', payload_size=0x100, row_stride=0x10, reserved=0
    tbl1_offset = 0x20
    tbcr_data = bytearray(struct.pack("<IIII", TBCR_MAGIC, 0x200, 1, 0))
    tbcr_data += struct.pack("<I", tbl1_offset)
    tbcr_data += bytes(tbl1_offset - len(tbcr_data))
    tbcr_data += struct.pack("<IIII", TBL1_MAGIC, 0x100, 0x10, 0)
    # Payload rows at TBCR_BASE + tbl1_offset + 0x10
    # 16 rows of 16 bytes: write distinct pattern
    for r in range(16):
        tbcr_data += struct.pack("<IIII", 0x1000 + r, 0x2000 + r, 0x3000 + r, 0x4000 + r)

    uc.mem_map(TBCR_BASE, TBCR_SIZE)
    uc.mem_write(TBCR_BASE, bytes(tbcr_data))

    uc.mem_map(STACK, STACK_SIZE)
    uc.reg_write(arm.UC_ARM_REG_SP, SP)
    uc.reg_write(arm.UC_ARM_REG_LR, STOP)

    uc.reg_write(arm.UC_ARM_REG_R0, 0x5000)  # dummy object
    uc.reg_write(arm.UC_ARM_REG_R1, index)   # profile index

    def hook_code(emu, address, size, user_data):
        if address == STOP:
            emu.emu_stop()

    uc.hook_add(unicorn.UC_HOOK_CODE, hook_code)
    uc.emu_start(0x002AEA28, STOP, timeout=500000)

    return {
        "r0": uc.reg_read(arm.UC_ARM_REG_R0),
        "sp": uc.reg_read(arm.UC_ARM_REG_SP),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "build/agent-work/H2-semantic/h2-global-tbb-lookup-convert-002c0ec4/run001")
    args = parser.parse_args()

    out_dir = args.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    orig_image = IMAGE.read_bytes()
    assert sha(orig_image) == IMAGE_SHA, f"Reference image hash mismatch: {sha(orig_image)}"

    body, relocs, compile_argv, obj_path = compile_body(out_dir)
    staged = stage_body(body, relocs)
    assert len(staged) == SLOT

    file_offset = ENTRY - CODE_BASE
    patched_image = orig_image[:file_offset] + staged + orig_image[file_offset + SLOT:]
    ips = make_ips(file_offset, staged)
    assert apply_ips(orig_image, ips) == patched_image, "IPS roundtrip mismatch"

    # Define direct cases
    test_slots = [0, 1, 2, 14, 0x41, 0x42, 0x43, 0x44, 0x50, 0x100, 0x7FFFFFFF, 0x80000000, 0xFFFFFFFF]
    test_indices = [0, 1, 2, 5, 0xFFFFFFFF]
    direct_cases = []

    # Valid container case
    tbcr_valid = build_tbcr(2, [0x20, 0x40])

    for s in test_slots:
        for idx in test_indices:
            direct_cases.append((s, idx, TBCR_BASE, tbcr_valid))
            # Also test with null container
            direct_cases.append((s, idx, 0, None))

    print(f"Running {len(direct_cases)} direct differential cases...")
    for s, idx, container_ptr, tbcr in direct_cases:
        orig_res = run_test(orig_image, s, idx, container_ptr, tbcr)
        patch_res = run_test(patched_image, s, idx, container_ptr, tbcr)

        assert orig_res["r0"] == patch_res["r0"], f"r0 mismatch on slot {s:#x}, idx {idx:#x}: orig={orig_res['r0']:#x}, patch={patch_res['r0']:#x}"
        assert orig_res["sp"] == patch_res["sp"], f"SP mismatch on slot {s:#x}"
        assert orig_res["call_events"] == patch_res["call_events"], f"Call events mismatch on slot {s:#x}: orig={orig_res['call_events']}, patch={patch_res['call_events']}"
        assert orig_res["mem_writes"] == patch_res["mem_writes"], f"Mem writes mismatch on slot {s:#x}"
        for r in ["r4", "r5", "r6", "r7", "r8", "r9", "r10", "r11"]:
            assert orig_res[r] == patch_res[r], f"{r} mismatch on slot {s:#x}"

    print(f"PASS: {len(direct_cases)} direct cases matched identically.")

    # Caller composition test through 0x002AEA28
    print("Running caller composition tests through 0x002AEA28...")
    caller_cases = [0, 1, 5, 15, 16, 20, 0xFFFFFFFF]
    for idx in caller_cases:
        orig_call = run_caller_test(orig_image, idx)
        patch_call = run_caller_test(patched_image, idx)
        assert orig_call["r0"] == patch_call["r0"], f"Caller r0 mismatch on idx {idx}: orig={orig_call['r0']:#x}, patch={patch_call['r0']:#x}"
        assert orig_call["sp"] == patch_call["sp"], f"Caller SP mismatch on idx {idx}"

    print(f"PASS: {len(caller_cases)} caller composition cases matched identically.")

    # Mutation controls
    print("Testing negative controls (mutations)...")
    controls = {
        "wrong_boundary_43": staged.replace(b"\x42\x00\x50\xe3", b"\x43\x00\x50\xe3"),  # cmp r0, #0x43 instead of 0x42
        "wrong_base_offset": staged.replace(b"\x30\x38\x49\x00", b"\x34\x38\x49\x00"),  # base +4 error
        "return_non_null_out_of_bounds": staged.replace(b"\x00\x00\xa0\x83", b"\x01\x00\xa0\x83"),  # movhi r0, #1
    }

    detected_mutants = []
    for name, mutant_staged in controls.items():
        if mutant_staged == staged:
            raise RuntimeError(f"Mutation {name} failed to apply")
        mutant_image = orig_image[:file_offset] + mutant_staged + orig_image[file_offset + SLOT:]
        # Find at least one case that fails
        detected = False
        for s, idx, container_ptr, tbcr in direct_cases:
            orig_res = run_test(orig_image, s, idx, container_ptr, tbcr)
            try:
                mut_res = run_test(mutant_image, s, idx, container_ptr, tbcr)
                if orig_res["r0"] != mut_res["r0"] or orig_res["call_events"] != mut_res["call_events"]:
                    detected = True
                    break
            except Exception:
                detected = True
                break
        assert detected, f"Mutant {name} was NOT detected!"
        detected_mutants.append(name)
        print(f"  Detected mutant: {name}")

    report = {
        "status": "passed",
        "entry": f"{ENTRY:#010x}",
        "size": SLOT,
        "direct_cases": len(direct_cases),
        "caller_cases": len(caller_cases),
        "detected_mutants": detected_mutants,
        "staged_sha256": sha(staged),
        "patched_image_sha256": sha(patched_image),
        "ips_sha256": sha(ips),
    }

    report_path = out_dir / "report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    (out_dir / "staged.bin").write_bytes(staged)
    (out_dir / "staged.ips").write_bytes(ips)
    print(f"Saved report to {report_path}")


if __name__ == "__main__":
    main()
