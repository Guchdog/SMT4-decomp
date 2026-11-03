#!/usr/bin/env python3
"""Final-VMA differential for engine_func_00227fe0 (0x00227FE0)."""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import struct
import sys
from pathlib import Path

import unicorn
from unicorn import arm_const as arm

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k

IMAGE = ROOT / "extracted/exefs/code.bin"
IMAGE_SHA = "1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558"
SOURCE = ROOT / "src/engine/leaf_batch30_c.cpp"
ENTRY, SLOT = 0x00227FE0, 128
CODE_BASE, CODE_SIZE = 0x00100000, 0x00380000
DATA_BASE, DATA_SIZE = 0x00500000, 0x00020000
STACK, STACK_SIZE = 0x08000000, 0x00010000
SP, STOP = STACK + 0x8000, STACK + 0x9000

GLOBAL_CONTEXT_ADDR = 0x00435D0C

TARGET_2C3290 = 0x002C3290
TARGET_2B45F8 = 0x002B45F8

TARGET_MAP = {
    "engine_func_002c3290": TARGET_2C3290,
    "engine_func_002b45f8": TARGET_2B45F8,
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def compile_body(out: Path, source: Path = SOURCE):
    out.mkdir(parents=True, exist_ok=True)
    obj = out / source.name.replace(".cpp", ".o")
    result = compile_tu_armv6k(source, obj, ROOT)
    if result.returncode != 0:
        raise RuntimeError(result.stderr or "ARMv6K translation unit compile failed")
    funcs = extract_elf_functions_detailed(obj)
    func_key = None
    for k in funcs:
        if "engine_func_00227fe0" in k or "00227fe0" in k:
            func_key = k
            break
    if not func_key:
        raise KeyError("engine_func_00227fe0 not found in compiled object")
    body, relocations = funcs[func_key]
    if len(body) > SLOT or len(body) % 4 != 0:
        raise ValueError(f"function body does not fit its slot: {len(body)}/{SLOT}")
    return body, relocations, list(result.args), obj


def stage_body(body: bytes, relocations) -> bytes:
    fixed = bytearray(body)
    if len(fixed) < SLOT:
        fixed.extend(b"\x00\x00\xa0\xe1" * ((SLOT - len(fixed)) // 4))
    for reloc in relocations:
        site = ENTRY + reloc.offset
        target = None
        for sym_prefix, sym_target in TARGET_MAP.items():
            if sym_prefix in reloc.symbol_name:
                target = sym_target
                break
        if target is None:
            raise KeyError(f"unmapped relocation symbol: {reloc.symbol_name}")
        delta = target - (site + 8)
        if target & 1 or delta & 3 or not -(1 << 25) <= delta < (1 << 25):
            raise ValueError(f"invalid ARM call target: {reloc}")
        imm24 = (delta >> 2) & 0x00FFFFFF
        insn = 0xEB000000 | imm24
        struct.pack_into("<I", fixed, reloc.offset, insn)
    return bytes(fixed)


def make_ips(offset: int, data: bytes) -> bytes:
    return b"PATCH" + struct.pack(">BH", (offset >> 16) & 0xFF, offset & 0xFFFF) + struct.pack(">H", len(data)) + data + b"EOF"


def apply_ips(base: bytes, ips: bytes) -> bytes:
    out = bytearray(base)
    idx = 5
    while idx < len(ips) - 3:
        offset = (ips[idx] << 16) | (ips[idx + 1] << 8) | ips[idx + 2]
        size = (ips[idx + 3] << 8) | ips[idx + 4]
        idx += 5
        out[offset:offset + size] = ips[idx:idx + size]
        idx += size
    return bytes(out)


def run_test(
    code_image: bytes,
    object_addr: int,
    base_addr: int,
    context_val: int,
    aux_val: int,
    hit_iteration: int,  # 0..3 for hit on that iteration, -1 for no hit
    halfwords: list[int],
) -> dict:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.mem_map(CODE_BASE, CODE_SIZE)
    uc.mem_write(CODE_BASE, code_image)

    # Write context at GLOBAL_CONTEXT_ADDR (inside CODE_BASE..CODE_BASE+CODE_SIZE)
    uc.mem_write(GLOBAL_CONTEXT_ADDR, struct.pack("<I", context_val))

    uc.mem_map(DATA_BASE, DATA_SIZE)
    uc.mem_write(DATA_BASE, bytes(DATA_SIZE))

    # Write base_addr at object_addr + 0x1CFC
    if object_addr != 0:
        uc.mem_write(object_addr + 0x1CFC, struct.pack("<I", base_addr))

    # If base_addr != 0, write halfwords at base_addr + 0x58 + i * 22 + 0x12
    if base_addr != 0:
        for i in range(4):
            entry_addr = base_addr + 0x58 + i * 22
            uc.mem_write(entry_addr + 0x12, struct.pack("<H", halfwords[i]))

    uc.mem_map(STACK, STACK_SIZE)
    uc.reg_write(arm.UC_ARM_REG_SP, SP)
    uc.reg_write(arm.UC_ARM_REG_LR, STOP)

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

    uc.reg_write(arm.UC_ARM_REG_R0, object_addr)

    call_events = []
    current_iter = [0]

    def hook_code(emu, address, size, user_data):
        if address == TARGET_2C3290:
            arg = emu.reg_read(arm.UC_ARM_REG_R0)
            call_events.append(("2c3290", arg))
            emu.reg_write(arm.UC_ARM_REG_R0, aux_val)
            emu.reg_write(arm.UC_ARM_REG_PC, emu.reg_read(arm.UC_ARM_REG_LR))
        elif address == TARGET_2B45F8:
            r0 = emu.reg_read(arm.UC_ARM_REG_R0)
            r1 = emu.reg_read(arm.UC_ARM_REG_R1)
            r2 = emu.reg_read(arm.UC_ARM_REG_R2)
            call_events.append(("2b45f8", r0, r1, r2))
            is_hit = current_iter[0] == hit_iteration
            current_iter[0] += 1
            # 0 on hit, 1 on miss
            ret_match = 0 if is_hit else 1
            emu.reg_write(arm.UC_ARM_REG_R0, ret_match)
            emu.reg_write(arm.UC_ARM_REG_PC, emu.reg_read(arm.UC_ARM_REG_LR))
        elif address == STOP:
            emu.emu_stop()

    uc.hook_add(unicorn.UC_HOOK_CODE, hook_code)
    uc.emu_start(ENTRY, STOP, timeout=500000)

    raw_r0 = uc.reg_read(arm.UC_ARM_REG_R0)
    signed_r0 = struct.unpack("<i", struct.pack("<I", raw_r0))[0]

    return {
        "raw_r0": raw_r0,
        "signed_r0": signed_r0,
        "sp": uc.reg_read(arm.UC_ARM_REG_SP),
        "r4": uc.reg_read(arm.UC_ARM_REG_R4),
        "r5": uc.reg_read(arm.UC_ARM_REG_R5),
        "r6": uc.reg_read(arm.UC_ARM_REG_R6),
        "r7": uc.reg_read(arm.UC_ARM_REG_R7),
        "r8": uc.reg_read(arm.UC_ARM_REG_R8),
        "r9": uc.reg_read(arm.UC_ARM_REG_R9),
        "r10": uc.reg_read(arm.UC_ARM_REG_R10),
        "r11": uc.reg_read(arm.UC_ARM_REG_R11),
        "call_events": call_events,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "build/agent-work/H2-semantic/engine-00227fe0/run001",
    )
    args = parser.parse_args()

    out_dir = args.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    orig_image = IMAGE.read_bytes()
    assert sha(orig_image) == IMAGE_SHA

    body, relocs, _, _ = compile_body(out_dir)
    staged = stage_body(body, relocs)
    assert len(staged) == SLOT

    file_offset = ENTRY - CODE_BASE
    patched_image = orig_image[:file_offset] + staged + orig_image[file_offset + SLOT:]
    ips = make_ips(file_offset, staged)
    assert apply_ips(orig_image, ips) == patched_image

    # Build cases
    cases = []

    # 1. Null base pointer -> returns -1 immediately
    cases.append((DATA_BASE, 0, 0x1234, 0x5678, -1, [100, 200, 300, 400]))

    # 2. Hits on iteration 0, 1, 2, 3
    for hit_it in (0, 1, 2, 3):
        cases.append((DATA_BASE, DATA_BASE + 0x4000, 0x1111, 0x2222, hit_it, [0x10, 0x20, 0x30, 0x40]))
        cases.append((DATA_BASE, DATA_BASE + 0x6000, 0x3333, 0x4444, hit_it, [0xABCD, 0x1234, 0x5678, 0x9ABC]))

    # 3. No hit on any iteration -> returns -1
    cases.append((DATA_BASE, DATA_BASE + 0x4000, 0x5555, 0x6666, -1, [0x11, 0x22, 0x33, 0x44]))

    # 4. Randomized fuzz matrix
    rng = random.Random(0x227FE0)
    for _ in range(50):
        c_hit = rng.choice([-1, 0, 1, 2, 3])
        hws = [rng.randint(0, 0xFFFF) for _ in range(4)]
        cases.append((
            DATA_BASE,
            DATA_BASE + 0x4000,
            rng.randint(0, 0xFFFFFFFF),
            rng.randint(0, 0xFFFFFFFF),
            c_hit,
            hws,
        ))

    print(f"Running {len(cases)} direct differential cases...")
    for idx, c in enumerate(cases):
        orig_res = run_test(orig_image, *c)
        patch_res = run_test(patched_image, *c)

        assert orig_res["signed_r0"] == patch_res["signed_r0"], (
            f"Case {idx} r0 mismatch: orig={orig_res['signed_r0']}, patch={patch_res['signed_r0']}"
        )
        assert orig_res["sp"] == patch_res["sp"]
        assert orig_res["call_events"] == patch_res["call_events"]
        for r in ["r4", "r5", "r6", "r7", "r8", "r9", "r10", "r11"]:
            assert orig_res[r] == patch_res[r]

    print(f"PASS: {len(cases)} direct differential cases matched identically.")

    # Mutation controls
    print("Testing negative controls (mutations)...")
    controls = {
        # Mutant 1: loop limit 3 instead of 4 (cmp r4, #0x58 instead of #0x6e)
        "mutant_loop_limit": staged.replace(b"\x6e\x00\x54\xe3", b"\x58\x00\x54\xe3"),
        # Mutant 2: invert hit condition (bne instead of beq on match check)
        "mutant_invert_hit": staged.replace(b"\xf1\xff\xff\x1a", b"\xf1\xff\xff\x0a"),
    }

    detected_mutants = []
    for name, mutant_staged in controls.items():
        if mutant_staged == staged:
            raise RuntimeError(f"Mutation {name} failed to apply")
        mutant_image = orig_image[:file_offset] + mutant_staged + orig_image[file_offset + SLOT:]
        detected = False
        for c in cases:
            orig_res = run_test(orig_image, *c)
            try:
                mut_res = run_test(mutant_image, *c)
                if (
                    orig_res["signed_r0"] != mut_res["signed_r0"]
                    or orig_res["call_events"] != mut_res["call_events"]
                ):
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
        "direct_cases": len(cases),
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
