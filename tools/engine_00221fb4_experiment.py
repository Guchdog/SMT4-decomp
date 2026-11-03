#!/usr/bin/env python3
"""Final-VMA differential for engine_func_00221fb4 (0x00221FB4)."""
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
ENTRY, SLOT = 0x00221FB4, 128
CODE_BASE, CODE_SIZE = 0x00100000, 0x00380000
DATA_BASE, DATA_SIZE = 0x00430000, 0x00020000  # covers 0x0043DF58
STACK, STACK_SIZE = 0x08000000, 0x00010000
SP, STOP = STACK + 0x8000, STACK + 0x9000

GLOBAL_HANDLE_ADDR = 0x0043DF58

TARGET_259510 = 0x00259510
TARGET_296F60 = 0x00296F60
TARGET_289640 = 0x00289640
TARGET_2BF41C = 0x002BF41C
TARGET_30A28C = 0x0030A28C

TARGET_MAP = {
    "engine_func_00259510": TARGET_259510,
    "engine_func_00296f60": TARGET_296F60,
    "engine_func_00289640": TARGET_289640,
    "battle_func_002bf41c": TARGET_2BF41C,
    "_3dEventEffect_func_0030a28c": TARGET_30A28C,
    "3dEventEffect_func_0030a28c": TARGET_30A28C,
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
        if "engine_func_00221fb4" in k or "00221fb4" in k:
            func_key = k
            break
    if not func_key:
        raise KeyError("engine_func_00221fb4 not found in compiled object")
    body, relocations = funcs[func_key]
    if len(body) > SLOT or len(body) % 4 != 0:
        raise ValueError(f"function body does not fit its slot: {len(body)}/{SLOT}")
    return body, relocations, list(result.args), obj


def stage_body(body: bytes, relocations) -> bytes:
    fixed = bytearray(body)
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
    init_handle: int,
    ret_259510: int,
    ret_296f60_1: int,
    ret_296f60_2: int,
    ret_296f60_3: int,
    ret_289640: int,
    ret_2bf41c: int,
    ret_30a28c: int,
) -> dict:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.mem_map(CODE_BASE, CODE_SIZE)
    uc.mem_write(CODE_BASE, code_image)

    uc.mem_write(GLOBAL_HANDLE_ADDR, struct.pack("<I", init_handle))

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

    call_events = []

    def hook_code(emu, address, size, user_data):
        if address == TARGET_259510:
            arg = emu.reg_read(arm.UC_ARM_REG_R0)
            call_events.append(("259510", arg))
            emu.reg_write(arm.UC_ARM_REG_R0, ret_259510)
            emu.reg_write(arm.UC_ARM_REG_PC, emu.reg_read(arm.UC_ARM_REG_LR))
        elif address == TARGET_296F60:
            arg = emu.reg_read(arm.UC_ARM_REG_R0)
            ret_val = (
                ret_296f60_1 if arg == 1 else (ret_296f60_2 if arg == 2 else ret_296f60_3)
            )
            call_events.append(("296f60", arg, ret_val))
            emu.reg_write(arm.UC_ARM_REG_R0, ret_val)
            emu.reg_write(arm.UC_ARM_REG_PC, emu.reg_read(arm.UC_ARM_REG_LR))
        elif address == TARGET_289640:
            call_events.append(("289640",))
            emu.reg_write(arm.UC_ARM_REG_R0, ret_289640)
            emu.reg_write(arm.UC_ARM_REG_PC, emu.reg_read(arm.UC_ARM_REG_LR))
        elif address == TARGET_2BF41C:
            arg = emu.reg_read(arm.UC_ARM_REG_R0)
            call_events.append(("2bf41c", arg))
            emu.reg_write(arm.UC_ARM_REG_R0, ret_2bf41c)
            emu.reg_write(arm.UC_ARM_REG_PC, emu.reg_read(arm.UC_ARM_REG_LR))
        elif address == TARGET_30A28C:
            r0 = emu.reg_read(arm.UC_ARM_REG_R0)
            r1 = emu.reg_read(arm.UC_ARM_REG_R1)
            r2 = emu.reg_read(arm.UC_ARM_REG_R2)
            r3 = emu.reg_read(arm.UC_ARM_REG_R3)
            call_events.append(("30a28c", r0, r1, r2, r3))
            emu.reg_write(arm.UC_ARM_REG_R0, ret_30a28c)
            emu.reg_write(arm.UC_ARM_REG_PC, emu.reg_read(arm.UC_ARM_REG_LR))
        elif address == STOP:
            emu.emu_stop()

    uc.hook_add(unicorn.UC_HOOK_CODE, hook_code)
    uc.emu_start(ENTRY, STOP, timeout=500000)

    final_handle = struct.unpack("<I", uc.mem_read(GLOBAL_HANDLE_ADDR, 4))[0]

    return {
        "r0": uc.reg_read(arm.UC_ARM_REG_R0),
        "sp": uc.reg_read(arm.UC_ARM_REG_SP),
        "r4": uc.reg_read(arm.UC_ARM_REG_R4),
        "r5": uc.reg_read(arm.UC_ARM_REG_R5),
        "r6": uc.reg_read(arm.UC_ARM_REG_R6),
        "r7": uc.reg_read(arm.UC_ARM_REG_R7),
        "r8": uc.reg_read(arm.UC_ARM_REG_R8),
        "r9": uc.reg_read(arm.UC_ARM_REG_R9),
        "r10": uc.reg_read(arm.UC_ARM_REG_R10),
        "r11": uc.reg_read(arm.UC_ARM_REG_R11),
        "final_handle": final_handle,
        "call_events": call_events,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "build/agent-work/H2-semantic/engine-00221fb4/run001",
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

    # Build direct test cases
    # (init_handle, ret_259510, ret_296f60_1, ret_296f60_2, ret_296f60_3, ret_289640, ret_2bf41c, ret_30a28c)
    cases = []

    # Branch 1: ret_289640 == 0 -> creates task via 30a28c, writes handle, returns 0
    for handle_init in (0, 0x1234, 0xDEADBEEF):
        for res_30a28c in (0x1000, 0xCAFEBABE):
            cases.append((handle_init, 10, 20, 30, 40, 0, 0, res_30a28c))

    # Branch 2: ret_289640 != 0, 2bf41c == 0 -> returns 1
    for handle_init in (0, 0x5555, 0x9999):
        cases.append((handle_init, 11, 22, 33, 44, 1, 0, 0x7777))
        cases.append((handle_init, 11, 22, 33, 44, 0x100, 0, 0x7777))

    # Branch 3: ret_289640 != 0, 2bf41c != 0 -> returns 0
    for handle_init in (0, 0x5555, 0x9999):
        for ret_bf41c in (1, 2, 0xFFFFFFFF):
            cases.append((handle_init, 11, 22, 33, 44, 1, ret_bf41c, 0x7777))

    # Randomized matrix
    rng = random.Random(0x221FB4)
    for _ in range(50):
        cases.append((
            rng.randint(0, 0xFFFFFFFF),
            rng.randint(0, 0xFFFF),
            rng.randint(0, 0xFFFF),
            rng.randint(0, 0xFFFF),
            rng.randint(0, 0xFFFF),
            rng.choice([0, 1, 2, 0x100]),
            rng.choice([0, 1, 2, 0xFFFFFFFF]),
            rng.randint(0, 0xFFFFFFFF),
        ))

    print(f"Running {len(cases)} direct differential cases...")
    for idx, c in enumerate(cases):
        orig_res = run_test(orig_image, *c)
        patch_res = run_test(patched_image, *c)

        assert orig_res["r0"] == patch_res["r0"], (
            f"Case {idx} r0 mismatch: orig={orig_res['r0']}, patch={patch_res['r0']}"
        )
        assert orig_res["final_handle"] == patch_res["final_handle"], (
            f"Case {idx} handle mismatch: orig={orig_res['final_handle']:#x}, patch={patch_res['final_handle']:#x}"
        )
        assert orig_res["sp"] == patch_res["sp"]
        assert orig_res["call_events"] == patch_res["call_events"]
        for r in ["r4", "r5", "r6", "r7", "r8", "r9", "r10", "r11"]:
            assert orig_res[r] == patch_res[r]

    print(f"PASS: {len(cases)} direct differential cases matched identically.")

    # Mutation controls
    print("Testing negative controls (mutations)...")
    controls = {
        # Mutant 1: invert condition on 2bf41c (e.g. return 0 when 2bf41c == 0)
        "mutant_invert_bf41c_ret": staged.replace(b"\xa0\x42\xa0\xe1", b"\x00\x40\xa0\xe3"),
        # Mutant 2: invert condition on 289640 (bne instead of beq)
        "mutant_invert_289640_branch": staged.replace(b"\x04\x00\x00\x0a", b"\x04\x00\x00\x1a"),
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
                    orig_res["r0"] != mut_res["r0"]
                    or orig_res["final_handle"] != mut_res["final_handle"]
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
