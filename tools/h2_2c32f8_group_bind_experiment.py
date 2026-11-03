#!/usr/bin/env python3
"""Pinned ARM differential for TitleConfig sprite-group binder 0x002C32F8."""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import struct
from pathlib import Path
import sys

import unicorn
from unicorn import arm_const as arm

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k
from tools.h2_calc_code_patch import apply_ips, encode_ips

IMAGE = ROOT / "extracted/exefs/code.bin"
IMAGE_SHA = "1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558"
SOURCE = ROOT / "src/engine/leaf_batch13_b.cpp"
ADDRESS, SPAN, CODE_BASE = 0x002C32F8, 76, 0x00100000
CODE_SIZE = 0x00378000
BLOCK, STACK, STACK_SIZE, RETURN = 0x00500000, 0x00600000, 0x10000, 0x00700000
SYMBOL = "camp_func_002c32f8"
CALLER_START, CALLER_STOP = 0x002F4D34, 0x002F4D6C
CALLEE = [(f"r{i}", getattr(arm, f"UC_ARM_REG_R{i}")) for i in range(4, 12)]
VFP_CALLEE = [(f"d{i}", getattr(arm, f"UC_ARM_REG_D{i}")) for i in range(8, 16)]


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def compile_body(out: Path) -> tuple[bytes, list, list[str], Path]:
    out.mkdir(parents=True, exist_ok=True)
    obj = out / "leaf_batch13_b.o"
    result = compile_tu_armv6k(SOURCE, obj, ROOT)
    if result.returncode:
        raise RuntimeError(result.stderr or "candidate TU compilation failed")
    entry = extract_elf_functions_detailed(obj).get(SYMBOL)
    if entry is None:
        raise ValueError(f"candidate symbol {SYMBOL!r} not found")
    body, relocs = entry
    if len(body) != SPAN or relocs:
        raise ValueError(f"candidate must be a 76-byte relocation-free body; got {len(body)} bytes / {relocs}")
    return body, list(relocs), list(result.args), obj


def stage(original: bytes, body: bytes) -> tuple[bytes, bytes]:
    off = ADDRESS - CODE_BASE
    staged = bytearray(original)
    staged[off:off + SPAN] = body
    staged = bytes(staged)
    ips = encode_ips([(off, body)], len(original))
    if apply_ips(original, ips) != staged:
        raise AssertionError("one-slot IPS replay failed")
    if original[:off] != staged[:off] or original[off + SPAN:] != staged[off + SPAN:]:
        raise AssertionError("staged replacement changed bytes outside target slot")
    return staged, ips


def fixed_cases(seed: int, random_count: int) -> list[dict]:
    fixed = [
        {"table": 0x00407EC6, "count": 0x18, "reg_word": 0,
         "stack": (0, 0, 0, 0, 0, 0, 0), "poison": 0xA5},
        {"table": 0xFFFFFFFF, "count": 0x12345678, "reg_word": 0x87654321,
         "stack": (0xABCDEF01, 0x10203040, 0xFEDCBA98, 0x55667788,
                   0x80000007, 0xA5A5A5A5, 0xDEADBEEF), "poison": 0x6D},
        {"table": 0, "count": 0xFFFFFFFF, "reg_word": 0x80000000,
         "stack": (0xFFFF0001, 0x7FC12345, 0x1234FFFF, 0x80000000,
                   0x89ABCDEF, 0x00000001, 0xFEDCBA98), "poison": 0xE3},
    ]
    rng = random.Random(seed)
    for _ in range(random_count):
        fixed.append({"table": rng.getrandbits(32), "count": rng.getrandbits(32),
                      "reg_word": rng.getrandbits(32),
                      "stack": tuple(rng.getrandbits(32) for _ in range(7)),
                      "poison": rng.randrange(1, 256)})
    return fixed


def init_uc(image: bytes, case: dict, n: int, caller: bool) -> tuple[unicorn.Uc, int, int]:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM | unicorn.UC_MODE_LITTLE_ENDIAN)
    uc.mem_map(CODE_BASE, CODE_SIZE)
    uc.mem_write(CODE_BASE, image)
    uc.mem_map(BLOCK, 0x1000)
    uc.mem_map(STACK, STACK_SIZE)
    uc.mem_map(RETURN, 0x1000)
    group = BLOCK + 0x300
    poison = bytes([case["poison"]]) * 0x20
    uc.mem_write(group, poison)
    sp = STACK + STACK_SIZE // 2
    uc.reg_write(arm.UC_ARM_REG_CPSR, 0x10)
    uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)
    uc.reg_write(arm.UC_ARM_REG_FPSCR, 0)
    for i, (_, reg) in enumerate(CALLEE):
        uc.reg_write(reg, 0xA5000000 | (n * 0x01010101 + i))
    for i, (_, reg) in enumerate(VFP_CALLEE):
        uc.reg_write(reg, 0x1122334455667700 + n * 8 + i)
    uc.reg_write(arm.UC_ARM_REG_SP, sp)
    uc.reg_write(arm.UC_ARM_REG_LR, RETURN)
    if caller:
        # Exact TitleConfig group-init/bind setup at 0x002F4D34..0x002F4D6C.
        uc.reg_write(arm.UC_ARM_REG_R4, group - 0x3C)
        uc.reg_write(arm.UC_ARM_REG_R5, 0)
    else:
        uc.mem_write(sp, struct.pack("<7I", *case["stack"]))
        uc.reg_write(arm.UC_ARM_REG_R0, group)
        uc.reg_write(arm.UC_ARM_REG_R1, case["table"])
        uc.reg_write(arm.UC_ARM_REG_R2, case["count"])
        uc.reg_write(arm.UC_ARM_REG_R3, case["reg_word"])
    return uc, group, sp


def run(image: bytes, case: dict, n: int, *, caller: bool = False) -> dict:
    uc, group, entry_sp = init_uc(image, case, n, caller)
    begin, until = (CALLER_START, CALLER_STOP) if caller else (ADDRESS, RETURN)
    fault = None
    try:
        uc.emu_start(begin, until, count=100000)
    except unicorn.UcError as exc:
        fault = str(exc)
    return {"fault": fault, "group": bytes(uc.mem_read(group, 0x20)),
            "return": uc.reg_read(arm.UC_ARM_REG_R0),
            "callee": tuple(uc.reg_read(reg) for _, reg in CALLEE),
            "vfp_callee": tuple(uc.reg_read(reg) for _, reg in VFP_CALLEE),
            "sp": uc.reg_read(arm.UC_ARM_REG_SP), "entry_sp": entry_sp,
            "pc": uc.reg_read(arm.UC_ARM_REG_PC)}


def compare(ref: dict, got: dict) -> str | None:
    for key in ("fault", "group", "return", "callee", "vfp_callee", "sp"):
        if ref[key] != got[key]:
            return f"{key} differs"
    if got["fault"] is not None:
        return "candidate faulted"
    if got["sp"] != got["entry_sp"]:
        return "candidate SP differs from entry"
    return None


def expected_group(case: dict, group: int) -> bytes:
    out = bytearray([case["poison"] & 0xFF]) * 0x20
    out[0:2] = struct.pack("<H", case["count"] & 0xFFFF)
    for offset, arg in zip((2, 4, 6, 8), (case["stack"][0], case["stack"][2],
                                           case["stack"][4], case["stack"][6])):
        struct.pack_into("<H", out, offset, arg & 0xFFFF)
    struct.pack_into("<5I", out, 0x0C, case["table"], case["reg_word"],
                     case["stack"][1], case["stack"][3], case["stack"][5])
    return bytes(out)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=20261102)
    parser.add_argument("--random-cases", type=int, default=48)
    args = parser.parse_args()
    out = args.out if args.out.is_absolute() else ROOT / args.out
    out.mkdir(parents=True, exist_ok=True)
    original = IMAGE.read_bytes()
    if sha(original) != IMAGE_SHA:
        raise ValueError("pinned original image SHA-256 mismatch")
    body, relocs, command, obj = compile_body(out / "compile")
    staged, ips = stage(original, body)
    (out / "candidate.ips").write_bytes(ips)
    (out / "candidate.bin").write_bytes(staged)

    failures, cases = [], []
    for i, case in enumerate(fixed_cases(args.seed, args.random_cases)):
        ref, got = run(original, case, i + 1), run(staged, case, i + 1)
        mismatch = compare(ref, got)
        if got["group"] != expected_group(case, BLOCK + 0x300):
            mismatch = mismatch or "independent descriptor expectation differs"
        row = {"index": i, "status": mismatch or "pass", "case": case,
               "return": f"0x{got['return']:08X}"}
        cases.append(row)
        if mismatch:
            failures.append(row)

    caller_case = fixed_cases(args.seed, 0)[0]
    caller_ref = run(original, caller_case, 0xC32F8, caller=True)
    caller_got = run(staged, caller_case, 0xC32F8, caller=True)
    caller_error = compare(caller_ref, caller_got)
    if caller_error:
        failures.append({"caller": caller_error})
    caller_initialized = {**caller_case, "poison": 0}
    if caller_got["group"] != expected_group(caller_initialized, BLOCK + 0x300):
        failures.append({"caller": "H2 descriptor expectation differs"})

    mutant_body = bytearray(body)
    # Remove the candidate's `strh r2, [r0]` count write at symbol offset 0x40.
    struct.pack_into("<I", mutant_body, 0x40, 0xE320F000)
    mutant_image, _ = stage(original, bytes(mutant_body))
    control_ref = run(original, fixed_cases(args.seed, 0)[1], 0xCC)
    control_mutant = run(mutant_image, fixed_cases(args.seed, 0)[1], 0xCC)
    control_difference = compare(control_ref, control_mutant)
    if control_difference is None:
        raise AssertionError("count-store negative control was not detected")

    report = {
        "target": "0x002C32F8", "original_image_sha256": sha(original),
        "original_span_sha256": sha(original[ADDRESS-CODE_BASE:ADDRESS-CODE_BASE+SPAN]),
        "candidate_source_sha256": sha(SOURCE.read_bytes()),
        "candidate_object_sha256": sha(obj.read_bytes()),
        "candidate_body_sha256": sha(body), "candidate_body_size": len(body),
        "slot_size": SPAN, "relocations": [str(x) for x in relocs],
        "compiler_command": command, "seed": args.seed,
        "case_count": len(cases), "cases": cases,
        "caller_slice": {"start": f"0x{CALLER_START:08X}",
                         "stop": f"0x{CALLER_STOP:08X}",
                         "status": caller_error or "pass",
                         "return": f"0x{caller_got['return']:08X}",
                         "descriptor": caller_got["group"].hex()},
        "negative_control": {"removed_store": "count halfword at +0",
                              "difference_detected": control_difference},
        "failures": failures, "status": "passed" if not failures else "failed",
        "domain": "ordinary aligned writable RAM; seven stack words copied as opaque raw bits; TitleConfig tuple uses zero tail words; resource table meaning is external",
    }
    (out / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"candidate={len(body)}/{SPAN} bytes; cases={len(cases)}; caller={caller_error or 'pass'}; failures={len(failures)}")
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
