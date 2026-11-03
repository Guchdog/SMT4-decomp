#!/usr/bin/env python3
"""Final-VMA differential for func_0024095c (0x0024095C)."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
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
ENTRY, SLOT = 0x0024095C, 128
CODE_BASE, CODE_SIZE = 0x00100000, 0x00380000
DATA_BASE, DATA_SIZE = 0x00500000, 0x00010000
STACK, STACK_SIZE = 0x08000000, 0x00010000
SP, STOP = STACK + 0x8000, STACK + 0x9000

OBJ_SIZE = 0x800


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
        if "func_0024095c" in k or "0024095c" in k:
            func_key = k
            break
    if not func_key:
        raise KeyError("func_0024095c not found in compiled object")
    body, relocations = funcs[func_key]
    if len(body) > SLOT or len(body) % 4 != 0:
        raise ValueError(f"function body does not fit its slot: {len(body)}/{SLOT}")
    return body, relocations, list(result.args), obj


def stage_body(body: bytes) -> bytes:
    fixed = bytearray(body)
    if len(fixed) < SLOT:
        fixed.extend(b"\x00\x00\xa0\xe1" * ((SLOT - len(fixed)) // 4))
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
    param: int,
    init_flags: int,
    v1: tuple[float, float, float],
    v2: tuple[float, float, float],
) -> dict:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.mem_map(CODE_BASE, CODE_SIZE)
    uc.mem_write(CODE_BASE, code_image)

    uc.mem_map(DATA_BASE, DATA_SIZE)
    obj_data = bytearray(OBJ_SIZE)

    # Write initial flags at 0x634
    struct.pack_into("<I", obj_data, 0x634, init_flags)
    # Write initial vectors
    # Vec 1: x at 0x0c, y at 0x10, z at 0x14
    struct.pack_into("<fff", obj_data, 0x0C, v1[0], v1[1], v1[2])
    # Vec 2: x at 0x18, y at 0x1c, z at 0x20
    struct.pack_into("<fff", obj_data, 0x18, v2[0], v2[1], v2[2])

    uc.mem_write(DATA_BASE, bytes(obj_data))

    uc.mem_map(STACK, STACK_SIZE)
    uc.reg_write(arm.UC_ARM_REG_SP, SP)
    uc.reg_write(arm.UC_ARM_REG_LR, STOP)

    # Enable VFP in Unicorn: write 0x40000000 to FPEXC
    uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)

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

    uc.reg_write(arm.UC_ARM_REG_R0, DATA_BASE)
    uc.reg_write(arm.UC_ARM_REG_R1, param)

    def hook_code(emu, address, size, user_data):
        if address == STOP:
            emu.emu_stop()

    uc.hook_add(unicorn.UC_HOOK_CODE, hook_code)
    uc.emu_start(ENTRY, STOP, timeout=500000)

    final_mem = uc.mem_read(DATA_BASE, OBJ_SIZE)

    return {
        "final_mem": bytes(final_mem),
        "sp": uc.reg_read(arm.UC_ARM_REG_SP),
        "r4": uc.reg_read(arm.UC_ARM_REG_R4),
        "r5": uc.reg_read(arm.UC_ARM_REG_R5),
        "r6": uc.reg_read(arm.UC_ARM_REG_R6),
        "r7": uc.reg_read(arm.UC_ARM_REG_R7),
        "r8": uc.reg_read(arm.UC_ARM_REG_R8),
        "r9": uc.reg_read(arm.UC_ARM_REG_R9),
        "r10": uc.reg_read(arm.UC_ARM_REG_R10),
        "r11": uc.reg_read(arm.UC_ARM_REG_R11),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "build/agent-work/H2-semantic/func-0024095c/run001",
    )
    args = parser.parse_args()

    out_dir = args.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    orig_image = IMAGE.read_bytes()
    assert sha(orig_image) == IMAGE_SHA

    body, _, _, _ = compile_body(out_dir)
    staged = stage_body(body)
    assert len(staged) == SLOT

    file_offset = ENTRY - CODE_BASE
    patched_image = orig_image[:file_offset] + staged + orig_image[file_offset + SLOT:]
    ips = make_ips(file_offset, staged)
    assert apply_ips(orig_image, ips) == patched_image

    # Build cases
    cases = []

    # 1. Distant points (dist >> 0.01)
    cases.append((0x1234, 0, (0.0, 0.0, 0.0), (1.0, 1.0, 1.0)))
    cases.append((0xABCD, 0x10000, (100.0, -50.0, 25.0), (-20.0, 30.0, -10.0)))

    # 2. Identical points (dist == 0.0 <= 0.01)
    cases.append((0x5555, 0, (5.0, 10.0, 15.0), (5.0, 10.0, 15.0)))
    cases.append((0x7777, 0x80000, (-1.0, -2.0, -3.0), (-1.0, -2.0, -3.0)))

    # 3. Near points (dist < 0.01)
    cases.append((0x8888, 0, (0.0, 0.0, 0.0), (0.001, 0.002, 0.002)))
    cases.append((0x9999, 0, (10.0, 20.0, 30.0), (10.003, 20.004, 30.005)))

    # 4. Boundary right around 0.01
    cases.append((0xAAAA, 0, (0.0, 0.0, 0.0), (0.009, 0.0, 0.0)))   # < 0.01
    cases.append((0xBBBB, 0, (0.0, 0.0, 0.0), (0.011, 0.0, 0.0)))   # > 0.01

    # 5. Randomized fixtures
    rng = random.Random(0x24095C)
    for _ in range(50):
        p = rng.randint(0, 0xFFFFFFFF)
        f = rng.randint(0, 0xFFFFFFFF)
        if rng.choice([True, False]):
            # Near points
            v1 = (rng.uniform(-100, 100), rng.uniform(-100, 100), rng.uniform(-100, 100))
            delta = rng.uniform(0.0, 0.008)
            v2 = (v1[0] + delta, v1[1], v1[2])
        else:
            # Distant points
            v1 = (rng.uniform(-100, 100), rng.uniform(-100, 100), rng.uniform(-100, 100))
            v2 = (rng.uniform(-100, 100), rng.uniform(-100, 100), rng.uniform(-100, 100))
        cases.append((p, f, v1, v2))

    print(f"Running {len(cases)} direct differential cases...")
    for idx, c in enumerate(cases):
        orig_res = run_test(orig_image, *c)
        patch_res = run_test(patched_image, *c)

        assert orig_res["final_mem"] == patch_res["final_mem"], (
            f"Case {idx} memory mismatch"
        )
        assert orig_res["sp"] == patch_res["sp"]
        for r in ["r4", "r5", "r6", "r7", "r8", "r9", "r10", "r11"]:
            assert orig_res[r] == patch_res[r]

    print(f"PASS: {len(cases)} direct differential cases matched identically.")

    # Mutation controls
    print("Testing negative controls (mutations)...")
    controls = {
        # Mutant 1: wrong bitmask 0x40000 instead of 0x80000 in orr
        "mutant_wrong_mask": staged.replace(b"\x02\x27\x81\xe3", b"\x01\x27\x81\xe3"),
        # Mutant 2: invert condition on bicls (bichi instead of bicls)
        "mutant_invert_thresh": staged.replace(b"\x02\x17\xc1\x93", b"\x02\x17\xc1\x83"),
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
                if orig_res["final_mem"] != mut_res["final_mem"]:
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
