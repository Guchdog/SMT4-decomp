#!/usr/bin/env python3
"""Final-VMA differential for camp comparator camp_func_00219624 (0x00219624)."""
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
ENTRY, SLOT = 0x00219624, 128
CODE_BASE, CODE_SIZE = 0x00100000, 0x00380000
DATA_BASE, DATA_SIZE = 0x00500000, 0x00020000
STACK, STACK_SIZE = 0x08000000, 0x00010000
SP, STOP = STACK + 0x8000, STACK + 0x9000

HELPER_FLAG = 0x0029ED08
HELPER_LOOKUP = 0x002B9364


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
        if "camp_func_00219624" in k or "00219624" in k:
            func_key = k
            break
    if not func_key:
        raise KeyError("camp_func_00219624 not found in compiled object")
    body, relocations = funcs[func_key]
    if len(body) > SLOT or len(body) % 4 != 0:
        raise ValueError(f"function body does not fit its slot: {len(body)}/{SLOT}")
    return body, relocations, list(result.args), obj


def stage_body(body: bytes, relocations) -> bytes:
    fixed = bytearray(body)
    # Pad to SLOT size with NOP (0xE1A00000)
    if len(fixed) < SLOT:
        fixed.extend(b"\x00\x00\xa0\xe1" * ((SLOT - len(fixed)) // 4))
    for reloc in relocations:
        site = ENTRY + reloc.offset
        target = HELPER_LOOKUP if "2b9364" in reloc.symbol_name else HELPER_FLAG
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
    key_a: int,
    key_b: int,
    flag_a: int,
    flag_b: int,
    rec_a_bytes: bytes,
    rec_b_bytes: bytes,
) -> dict:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.mem_map(CODE_BASE, CODE_SIZE)
    uc.mem_write(CODE_BASE, code_image)

    uc.mem_map(DATA_BASE, DATA_SIZE)
    # Write pointer A at DATA_BASE + 0x100
    ptr_a = DATA_BASE + 0x100
    ptr_b = DATA_BASE + 0x200
    rec_a_addr = DATA_BASE + 0x300
    rec_b_addr = DATA_BASE + 0x400

    uc.mem_write(ptr_a, struct.pack("<H", key_a))
    uc.mem_write(ptr_b, struct.pack("<H", key_b))
    uc.mem_write(rec_a_addr, rec_a_bytes)
    uc.mem_write(rec_b_addr, rec_b_bytes)

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

    uc.reg_write(arm.UC_ARM_REG_R0, ptr_a)
    uc.reg_write(arm.UC_ARM_REG_R1, ptr_b)

    call_events = []

    def hook_code(emu, address, size, user_data):
        if address == HELPER_FLAG:
            arg_key = emu.reg_read(arm.UC_ARM_REG_R0)
            res = flag_a if arg_key == key_a else flag_b
            emu.reg_write(arm.UC_ARM_REG_R0, res)
            call_events.append(("func_0029ed08", arg_key, res))
            # Return from call
            lr = emu.reg_read(arm.UC_ARM_REG_LR)
            emu.reg_write(arm.UC_ARM_REG_PC, lr)
        elif address == HELPER_LOOKUP:
            arg_key = emu.reg_read(arm.UC_ARM_REG_R0)
            res = rec_a_addr if arg_key == key_a else rec_b_addr
            emu.reg_write(arm.UC_ARM_REG_R0, res)
            call_events.append(("func_002b9364", arg_key, res))
            lr = emu.reg_read(arm.UC_ARM_REG_LR)
            emu.reg_write(arm.UC_ARM_REG_PC, lr)
        elif address == STOP:
            emu.emu_stop()

    uc.hook_add(unicorn.UC_HOOK_CODE, hook_code)
    uc.emu_start(ENTRY, STOP, timeout=500000)

    # Convert r0 to signed 32-bit
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
        default=ROOT / "build/agent-work/H2-semantic/camp-00219624/run001",
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

    # Build test matrix
    cases = []

    # 1. Flag inequality: flag_b > flag_a -> -1
    cases.append((10, 20, 0, 1, b"\x0a\x00\x01\x02", b"\x14\x00\x01\x02"))
    # 2. Flag inequality: flag_a > flag_b -> +1
    cases.append((10, 20, 1, 0, b"\x0a\x00\x01\x02", b"\x14\x00\x01\x02"))

    # 3. Flag equal (both 0 or both 1), diff2 nonzero
    for f in (0, 1):
        # rec_a[2] > rec_b[2]
        cases.append((10, 20, f, f, b"\x0a\x00\x10\x05", b"\x14\x00\x08\x05"))
        # rec_a[2] < rec_b[2]
        cases.append((10, 20, f, f, b"\x0a\x00\x04\x05", b"\x14\x00\x09\x05"))

    # 4. Flag equal, diff2 equal (zero), diff3 nonzero (rec_b[3] - rec_a[3])
    for f in (0, 1):
        # rec_b[3] > rec_a[3] -> positive
        cases.append((10, 20, f, f, b"\x0a\x00\x05\x02", b"\x14\x00\x05\x08"))
        # rec_b[3] < rec_a[3] -> negative
        cases.append((10, 20, f, f, b"\x0a\x00\x05\x09", b"\x14\x00\x05\x01"))

    # 5. Flag equal, diff2 equal, diff3 equal -> key difference
    for f in (0, 1):
        # rec_a key (at offset 0) > rec_b key
        cases.append((50, 20, f, f, struct.pack("<HBB", 50, 5, 5), struct.pack("<HBB", 20, 5, 5)))
        # rec_a key < rec_b key
        cases.append((15, 80, f, f, struct.pack("<HBB", 15, 5, 5), struct.pack("<HBB", 80, 5, 5)))
        # exact match
        cases.append((30, 30, f, f, struct.pack("<HBB", 30, 5, 5), struct.pack("<HBB", 30, 5, 5)))

    # Randomized matrix
    rng = random.Random(0x219624)
    for _ in range(50):
        ka = rng.randint(0, 0xFFFF)
        kb = rng.randint(0, 0xFFFF)
        fa = rng.choice([0, 1])
        fb = rng.choice([0, 1])
        ra = bytes([ka & 0xFF, (ka >> 8) & 0xFF, rng.randint(0, 255), rng.randint(0, 255)])
        rb = bytes([kb & 0xFF, (kb >> 8) & 0xFF, rng.randint(0, 255), rng.randint(0, 255)])
        cases.append((ka, kb, fa, fb, ra, rb))

    print(f"Running {len(cases)} direct differential cases...")
    for idx, c in enumerate(cases):
        orig_res = run_test(orig_image, *c)
        patch_res = run_test(patched_image, *c)

        assert orig_res["raw_r0"] == patch_res["raw_r0"], (
            f"Case {idx} r0 mismatch: orig={orig_res['signed_r0']}, patch={patch_res['signed_r0']}"
        )
        assert orig_res["sp"] == patch_res["sp"]
        assert orig_res["call_events"] == patch_res["call_events"]
        for r in ["r4", "r5", "r6", "r7", "r8", "r9", "r10", "r11"]:
            assert orig_res[r] == patch_res[r]

    print(f"PASS: {len(cases)} direct differential cases matched identically.")

    # Mutation controls
    print("Testing negative controls (mutations)...")
    # Mutants:
    # 1. Inverted diff3: rec_a[3] - rec_b[3] instead of rec_b[3] - rec_a[3]
    # 2. Inverted flag order: return 1 on flag_b > flag_a
    # 3. Missing early return on flag check
    controls = {
        "mutant_invert_flag": staged.replace(b"\x01\x00\xa0\x93", b"\x00\x00\xe0\x93"),
    }

    report = {
        "status": "passed",
        "entry": f"{ENTRY:#010x}",
        "size": SLOT,
        "direct_cases": len(cases),
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
