#!/usr/bin/env python3
"""Compare the isolated 0x0015555C callback with readable ARM C++.

Uses a private ARM object and Unicorn only; it does not enter the surrounding
H1 callback or infer which runtime asset selects this callback.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.asm_diff import extract_elf_functions_detailed  # noqa: E402
from tools.build_check import compile_tu_armv6k  # noqa: E402
from tools.semantic_experiment import TEXT, unicorn, arm, require_unicorn  # noqa: E402

REFERENCE_SHA256 = "1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558"
ENTRY = 0x0015555C
PREDECESSOR_RETURN = 0x00155558
END = 0x00155584
INJECT = 0x01000000
STOP = INJECT + 0x1000
DATA = 0x02000000
STACK = 0x08000000
SP = STACK + 0x1000
SOURCE = ROOT / "experiments/semantic_equivalence/h1_type0_callback_candidate.cpp"


def fbits(value: float) -> int:
    return struct.unpack("<I", struct.pack("<f", value))[0]


def fvalue(bits: int) -> float:
    return struct.unpack("<f", struct.pack("<I", bits))[0]


def compile_object(output: Path) -> tuple[Path, dict[str, bytes], dict[str, str]]:
    output.mkdir(parents=True, exist_ok=True)
    obj = output / "h1_type0_callback.o"
    result = compile_tu_armv6k(SOURCE, obj, ROOT)
    (output / "compile.stdout.txt").write_text(result.stdout, encoding="utf-8")
    (output / "compile.stderr.txt").write_text(result.stderr, encoding="utf-8")
    if result.returncode:
        raise RuntimeError(f"ARM compile failed ({result.returncode}): {result.stderr}")
    funcs = extract_elf_functions_detailed(obj)
    code: dict[str, bytes] = {}
    for name in ("h1_type0_callback", "h1_type0_callback_wrong_nan"):
        body, relocs = funcs[name]
        if relocs:
            raise RuntimeError(f"unexpected relocations in {name}: {relocs}")
        code[name] = body
    return obj, code, {k: hashlib.sha256(v).hexdigest() for k, v in code.items()}


def execute(image: bytes, body: bytes, args: tuple[int, int, int], start: int) -> dict:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.ctl_set_cpu_model(arm.UC_CPU_ARM_11MPCORE)
    uc.mem_map(TEXT, 0x400000, unicorn.UC_PROT_READ | unicorn.UC_PROT_EXEC)
    uc.mem_write(TEXT, image)
    uc.mem_map(INJECT, 0x2000, unicorn.UC_PROT_READ | unicorn.UC_PROT_EXEC)
    uc.mem_map(DATA, 0x1000, unicorn.UC_PROT_READ | unicorn.UC_PROT_WRITE)
    uc.mem_map(STACK, 0x2000, unicorn.UC_PROT_READ | unicorn.UC_PROT_WRITE)
    if body:
        uc.mem_write(INJECT, body)
        start = INJECT
    uc.reg_write(arm.UC_ARM_REG_C1_C0_2, 0x00F00000)
    uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)
    uc.reg_write(arm.UC_ARM_REG_CPSR, 0x10)
    # Sentinel values prove the integer and VFP callee-saved registers survive.
    for i in range(13):
        uc.reg_write(getattr(arm, f"UC_ARM_REG_R{i}"), (0xA5A50000 + i) & 0xFFFFFFFF)
    uc.reg_write(arm.UC_ARM_REG_SP, SP)
    uc.reg_write(arm.UC_ARM_REG_LR, STOP)
    for i, bits in enumerate(args):
        uc.reg_write(getattr(arm, f"UC_ARM_REG_S{i}"), bits)
    for i in range(8, 16):
        uc.reg_write(getattr(arm, f"UC_ARM_REG_D{i}"), 0x1122334455667700 + i)
    data_before = bytes([0x5A]) * 0x1000
    stack_before = bytes([0xC3]) * 0x2000
    uc.mem_write(DATA, data_before)
    uc.mem_write(STACK, stack_before)
    writes: list[dict] = []

    def on_mem(machine, access, address, size, value, _):
        if access == unicorn.UC_MEM_WRITE:
            writes.append({"address": hex(address), "size": size,
                           "value": hex(value & ((1 << (size * 8)) - 1))})

    def on_code(machine, address, _size, _):
        if address == STOP:
            machine.emu_stop()

    uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, on_mem)
    uc.hook_add(unicorn.UC_HOOK_CODE, on_code)
    fault = None
    try:
        uc.emu_start(start, 0, count=128)
    except unicorn.UcError as exc:
        fault = f"{exc} at pc={uc.reg_read(arm.UC_ARM_REG_PC):#x}"
    return {
        "stopped": uc.reg_read(arm.UC_ARM_REG_PC) == STOP,
        "fault": fault,
        "s0": uc.reg_read(arm.UC_ARM_REG_S0),
        "fpscr": uc.reg_read(arm.UC_ARM_REG_FPSCR),
        "preserved_r4_r11": [uc.reg_read(getattr(arm, f"UC_ARM_REG_R{i}")) for i in range(4, 12)],
        "sp": uc.reg_read(arm.UC_ARM_REG_SP),
        "preserved_d8_d15": [uc.reg_read(getattr(arm, f"UC_ARM_REG_D{i}")) for i in range(8, 16)],
        "writes": writes,
        "data_unchanged": bytes(uc.mem_read(DATA, 0x1000)) == data_before,
        "stack_unchanged": bytes(uc.mem_read(STACK, 0x2000)) == stack_before,
    }


def cases() -> list[tuple[str, int, int, int]]:
    nan_q = 0x7FC00001
    nan_neg = 0xFFC00001
    return [
        ("inside", fbits(0.0), fbits(1.0), fbits(0.5)),
        ("at-lower", fbits(0.0), fbits(1.0), fbits(0.0)),
        ("below-lower", fbits(0.0), fbits(1.0), fbits(-0.25)),
        ("at-upper", fbits(0.0), fbits(1.0), fbits(1.0)),
        ("above-upper", fbits(0.0), fbits(1.0), fbits(1.25)),
        ("reversed-inside", fbits(1.0), fbits(0.0), fbits(0.5)),
        ("reversed-below", fbits(1.0), fbits(0.0), fbits(-0.5)),
        ("reversed-above", fbits(1.0), fbits(0.0), fbits(1.5)),
        ("equal", fbits(0.5), fbits(0.5), fbits(-2.0)),
        ("unordered-value", fbits(0.0), fbits(1.0), nan_q),
        ("unordered-negative", fbits(-1.0), fbits(1.0), nan_neg),
        ("unordered-upper", fbits(0.0), nan_q, fbits(0.5)),
        ("unordered-lower", nan_q, fbits(1.0), fbits(0.5)),
        ("positive-infinity", fbits(-1.0), fbits(1.0), fbits(float("inf"))),
        ("negative-infinity", fbits(-1.0), fbits(1.0), fbits(float("-inf"))),
        ("signed-zero-minus", fbits(-0.0), fbits(1.0), fbits(-0.0)),
        ("signed-zero-plus", fbits(-0.0), fbits(1.0), fbits(0.0)),
    ]


def same(a: dict, b: dict) -> bool:
    return all(a[k] == b[k] for k in (
        "stopped", "fault", "s0", "fpscr", "preserved_r4_r11", "sp",
        "preserved_d8_d15", "writes", "data_unchanged", "stack_unchanged"))


def experiment(code_path: Path, output: Path) -> dict:
    require_unicorn()
    image = code_path.read_bytes()
    digest = hashlib.sha256(image).hexdigest()
    if digest != REFERENCE_SHA256:
        raise ValueError(f"unexpected code.bin SHA-256 {digest}")
    obj, functions, code_hashes = compile_object(output)
    report_cases = []
    controls = []
    for label, low, high, value in cases():
        args = (low, high, value)
        original = execute(image, b"", args, ENTRY)
        candidate = execute(image, functions["h1_type0_callback"], args, INJECT)
        row = {"case": label, "lower": hex(low), "upper": hex(high), "value": hex(value),
               "original": original, "candidate": candidate, "matched": same(original, candidate)}
        report_cases.append(row)
        if not row["matched"]:
            raise AssertionError(f"differential mismatch in {label}: {row}")
    # The ordered-comparison mutant preserves NaN result bits, but its quiet
    # comparison lowering omits the invalid-status update produced by VCMPE.
    for label, low, high, value in cases():
        if "unordered" not in label:
            continue
        original = execute(image, b"", (low, high, value), ENTRY)
        wrong = execute(image, functions["h1_type0_callback_wrong_nan"], (low, high, value), INJECT)
        if original["s0"] != wrong["s0"]:
            raise AssertionError(f"negative control unexpectedly changed s0 on {label}")
        if original["fpscr"] == wrong["fpscr"]:
            raise AssertionError(f"negative control unexpectedly preserved FPSCR on {label}")
        controls.append({"case": label, "rejected": True, "same_s0": True,
                         "fpscr_differs": True,
                         "reason": "same return s0, but quiet comparison omits VCMPE invalid-status update",
                         "original_s0": hex(original["s0"]), "wrong_s0": hex(wrong["s0"]),
                         "original_fpscr": hex(original["fpscr"]), "wrong_fpscr": hex(wrong["fpscr"])})
    report = {
        "passed": True,
        "evidence_type": "isolated-entry: pinned ARM instructions vs compiled hard-float ARM C++",
        "code_sha256": digest,
        "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "object_sha256": hashlib.sha256(obj.read_bytes()).hexdigest(),
        "candidate_code_sha256": code_hashes,
        "entry": hex(ENTRY), "predecessor_return": hex(PREDECESSOR_RETURN), "original_body_end": hex(END),
        "boundary_proof": "Pinned entry begins at 0x0015555C immediately after 0x00155540's bx/pop return at 0x00155558; callback registration stores the literal 0x0015555C and indirect call sites use BLX. Tests enter 0x0015555C directly and stop at LR.",
        "abi": "AAPCS hard-float: lower=s0, upper=s1, value=s2; result=s0. r4-r11, SP, d8-d15 preserved; no callback memory writes.",
        "unordered_vcmpe": "NZCV=0011; GT=false and LO=false. An unordered input value therefore remains unchanged in s0; VCMPE still raises FPSCR invalid-operation status for quiet NaN operands.",
        "cases": report_cases, "negative_controls": controls,
        "limits": [
            "Static registration and synthetic original transition traces establish a reachable callback path, but do not establish which live H1 source object selects it.",
            "No live emulator, asset-selection, renderer, or whole-caller equivalence is claimed.",
            "FPSCR is compared as reported by Unicorn; this is bounded ARM emulation evidence, not physical hardware validation.",
        ],
    }
    output.mkdir(parents=True, exist_ok=True)
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code", type=Path, default=ROOT / "extracted/exefs/code.bin")
    parser.add_argument("--output", type=Path, required=True, help="fresh task-private output directory")
    args = parser.parse_args()
    report = experiment(args.code, args.output)
    print(f"isolated H1 type-0 callback PASS: {len(report['cases'])} cases, {len(report['negative_controls'])} negative controls")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
