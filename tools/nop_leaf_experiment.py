#!/usr/bin/env python3
"""Differential experiment for three exact ARM no-op leaves.

The originals are `mov r0, r0; bx lr`. This experiment tests only the raw
observable identity contract (registers, NZCV, memory, and continuation), not
an inferred source-level signature or complete-game behavior. Reports and
objects stay under unique ignored build/ paths.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import random
import struct
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import capstone
from tools.build_check import find_clang
from tools.semantic_experiment import (
    DATA, DATA_SIZE, STACK_SIZE, TEXT, Case, Runner, difference,
)
from tools.semantic_experiment_support import (
    compile_candidate_symbols, load_pinned_reference,
)

ADDRESSES = (0x0023A350, 0x0036A29C, 0x00381464)
EXPECTED = (("mov", "r0, r0"), ("bx", "lr"))
SEEDS = (7, 20261024)
U32_MASK = 0xFFFFFFFF


class FullStateRunner(Runner):
    """Also capture caller-saved GPRs omitted from the shared ABI comparator."""

    def run(self, case: Case, **kwargs):
        execution = super().run(case, **kwargs)
        from tools import semantic_experiment as semantic
        self.observed_gprs = tuple(
            self.uc.reg_read(getattr(semantic.arm, f"UC_ARM_REG_R{i}"))
            for i in range(13)
        ) + (
            self.uc.reg_read(semantic.arm.UC_ARM_REG_SP),
            self.uc.reg_read(semantic.arm.UC_ARM_REG_LR),
        )
        return execution


def verify_reference(image: bytes, game_info: dict, ledger: list[dict]) -> dict:
    expected_hash = str(game_info.get("code_sha256", "")).lower()
    digest = hashlib.sha256(image).hexdigest()
    if digest != expected_hash:
        raise ValueError("code.bin SHA-256 does not match the pinned game revision")
    if len(image) != int(game_info["code_bin_size"]):
        raise ValueError("code.bin size does not match the pinned game revision")

    by_address = {int(row["address"], 16): row for row in ledger}
    decoder = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    functions = {}
    for address in ADDRESSES:
        row = by_address.get(address)
        if row is None or row["status"].strip() != "matching" or int(row["size"]) != 8:
            raise ValueError(f"Missing matching 8-byte ledger row at {address:#010x}")
        offset = address - TEXT
        raw = image[offset:offset + 8]
        decoded = list(decoder.disasm(raw, address))
        actual = tuple((insn.mnemonic.lower(), insn.op_str.lower()) for insn in decoded)
        if actual != EXPECTED or sum(insn.size for insn in decoded) != 8:
            raise ValueError(f"Original instruction sequence changed at {address:#010x}: {actual}")
        functions[hex(address)] = {
            "name": row["name"],
            "category": row["category"],
            "size": len(raw),
            "original_bytes_hex": raw.hex(),
            "original_bytes_sha256": hashlib.sha256(raw).hexdigest(),
            "instructions": [f"{mnemonic} {operands}" for mnemonic, operands in actual],
            "contract_under_test": "identity of r0-r12, SP, LR, NZCV, RAM, access footprint, and return continuation",
        }
    return {"code_sha256": digest, "functions": functions}


def _case(address: int, seed: int, index: int) -> Case:
    rng = random.Random(seed ^ address ^ (index * 0x9E3779B1))
    data = bytearray(rng.randbytes(DATA_SIZE))
    regs = [rng.getrandbits(32) for _ in range(13)]
    # Include zero, high-bit, and ordinary values, then retain broad random GPR
    # state so an accidental clobber in any register is observable.
    regs[0] = (0, 1, 0x12345678, 0x80000000, U32_MASK)[index % 5]
    nzcv = (0x00000000, 0x40000000, 0x80000000, 0xC0000000)[index % 4]
    return Case(f"case-{index}", tuple(regs), bytes(data), rng.randbytes(STACK_SIZE), nzcv)


def make_cases(address: int, samples: int, seed: int):
    # Four flag states are guaranteed before seeded randomized repetitions.
    for index in range(4 + samples):
        yield _case(address, seed, index)


def _compare(original_runner: FullStateRunner, candidate_runner: FullStateRunner,
             case: Case) -> str | None:
    original = original_runner.run(case)
    candidate = candidate_runner.run(case)
    reason = difference(original, candidate, returns_value=True, compare_flags=True)
    if reason:
        return reason
    if original_runner.observed_gprs != candidate_runner.observed_gprs:
        return "general-purpose register / SP / LR state differs"
    return None


def run(code_path: Path, output: Path, samples: int = 64,
        seed: int = 20261024) -> dict:
    if samples < 0:
        raise ValueError("samples must be non-negative")
    output.mkdir(parents=True, exist_ok=True)
    pinned = load_pinned_reference(
        code_path, ROOT / "config/game_info.json", ROOT / "config/functions.csv"
    )
    reference = verify_reference(pinned.image, pinned.game_info, pinned.ledger)
    source = ROOT / "experiments/semantic_equivalence/nop_leaf_candidates.cpp"
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    symbols = compile_candidate_symbols(
        source, output / "nop_leaf_candidates.o", ROOT,
        {f"candidate_{address:08x}" for address in ADDRESSES} | {
            "negative_clobber_r0", "negative_clobber_r1",
            "negative_clobber_flags", "negative_write_memory",
        },
    )

    results = []
    for address in ADDRESSES:
        symbol = f"candidate_{address:08x}"
        original_runner = FullStateRunner(pinned.image, address)
        candidate_runner = FullStateRunner(
            pinned.image, address, symbols[symbol]
        )
        passed, failure, count = True, None, 0
        for case in make_cases(address, samples, seed):
            count += 1
            reason = _compare(original_runner, candidate_runner, case)
            if reason:
                passed, failure = False, {"case": case.label, "reason": reason}
                break
        results.append({
            "address": hex(address), "candidate": symbol,
            "original_bytes": 8, "candidate_bytes": len(symbols[symbol]),
            "passed": passed, "cases": count, "failure": failure,
        })

    # Each control gets an input tailored to the state it wrongly changes.
    control_setup = (
        ("negative_clobber_r0", "r0", 0),
        ("negative_clobber_r1", "r1", 1),
        ("negative_clobber_flags", "nzcv", 0x40000000),
        ("negative_write_memory", "memory", 0),
    )
    controls = []
    for control_index, (symbol, kind, _) in enumerate(control_setup):
        address = ADDRESSES[control_index % len(ADDRESSES)]
        case = _case(address, seed + 91, 5 + control_index)
        regs, data = list(case.registers), bytearray(case.data)
        if kind == "r0":
            regs[0] = DATA + 0x100
        elif kind == "r1":
            regs[1] = 0x12345678
        elif kind == "memory":
            regs[0] = DATA + 0x100
            struct.pack_into("<I", data, 0x100, 0xA5A55A5A)
        tailored = Case(case.label + "-control", tuple(regs), bytes(data),
                        case.stack, 0x40000000 if kind == "nzcv" else case.nzcv)
        original_runner = FullStateRunner(pinned.image, address)
        wrong_runner = FullStateRunner(pinned.image, address, symbols[symbol])
        reason = _compare(original_runner, wrong_runner, tailored)
        controls.append({"name": symbol, "target": hex(address),
                         "state_targeted": kind, "detected": reason is not None,
                         "reason": reason})

    if hashlib.sha256(source.read_bytes()).hexdigest() != source_hash:
        raise RuntimeError("Candidate source changed during the experiment")
    compiler = subprocess.run([str(find_clang()), "--version"], capture_output=True,
                              text=True, check=True)
    report = {
        "schema": 1,
        "passed": all(row["passed"] for row in results)
                  and all(row["detected"] for row in controls),
        "scope": "three isolated no-op leaf candidates; no production source or game boot",
        "reference_sha256": reference["code_sha256"],
        "pinned_functions": reference["functions"],
        "source_sha256": source_hash,
        "object_sha256": hashlib.sha256((output / "nop_leaf_candidates.o").read_bytes()).hexdigest(),
        "compiler": compiler.stdout.splitlines()[0],
        "seed": seed,
        "random_samples_per_function": samples,
        "function_comparisons": sum(row["cases"] for row in results),
        "functions": results,
        "caller_windows_executed": 0,
        "negative_controls": controls,
        "limitations": [
            "The inferred source-level argument and return types are intentionally unknown; only the raw identity/no-side-effect contract is tested.",
            "This is bounded Unicorn differential evidence, not formal equivalence or a complete-game test.",
            "The shared test memory covers ordinary RAM; MMIO, concurrent observers, faults, and timing are not tested.",
            "Caller windows were not run. Matching direct-BL xrefs are not runtime evidence and would require manual containing-function review.",
            "Candidates are experiment-only and do not modify production sources, the matching ledger, or game image.",
        ],
    }
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n",
                                         encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code", type=Path, default=ROOT / "extracted/exefs/code.bin")
    parser.add_argument("--output", type=Path,
                        default=ROOT / "build/semantic-equivalence/nop-leaf-seed20261024")
    parser.add_argument("--samples", type=int, default=64)
    parser.add_argument("--seed", type=int, default=20261024)
    args = parser.parse_args()
    try:
        report = run(args.code, args.output, args.samples, args.seed)
    except (RuntimeError, ValueError, OSError) as error:
        parser.exit(2, f"Experiment error: {error}\n")
    print(f"No-op leaf experiment {'PASS' if report['passed'] else 'FAIL'}; "
          f"{report['function_comparisons']} function cases; "
          f"report: {args.output / 'report.json'}", flush=True)
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
