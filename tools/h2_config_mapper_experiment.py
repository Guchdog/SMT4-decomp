#!/usr/bin/env python3
"""Exhaustive byte-domain ARM comparison for titleConfig's three mappers."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import random
import subprocess
import sys
import time

import capstone
import unicorn

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k, find_clang
from tools.semantic_experiment import Case, Runner

MAPPERS = {
    0x002CAB70: ("candidate_002cab70", (0, 10, 20, 25, 30, 35, 40, 45, 50, 70, 90)),
    0x0021F39C: ("candidate_0021f39c", (0, 10, 20, 30, 40, 50, 60, 70, 80, 100, 120)),
    0x002E0AF4: ("candidate_002e0af4", (0, 10, 20, 30, 40, 50, 60, 70, 80, 100, 120)),
}
WRONG = "candidate_002cab70_wrong_map"
SOURCE = ROOT / "experiments/semantic_equivalence/h2_config_mapper_candidates.cpp"
CODE_DEFAULT = ROOT / "extracted/exefs/code.bin"


def validate_mapper_blob(code: bytes) -> None:
    """Allow local conditional returns/branches; reject calls and PC-relative code."""
    decoder = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    decoder.detail = True
    instructions = list(decoder.disasm(code, 0))
    if not instructions or sum(i.size for i in instructions) != len(code):
        raise ValueError("Incomplete mapper disassembly")
    if instructions[-1].mnemonic != "bx" or instructions[-1].op_str != "lr":
        raise ValueError("Mapper blob must end in bx lr")
    for instruction in instructions[:-1]:
        if instruction.group(capstone.CS_GRP_CALL):
            raise ValueError("Mapper candidate unexpectedly calls another function")
        if instruction.group(capstone.CS_GRP_JUMP):
            if instruction.mnemonic.startswith("bx") and instruction.op_str == "lr":
                continue
            if not instruction.operands or instruction.operands[0].type != capstone.CS_OP_IMM:
                raise ValueError("Mapper candidate has a non-local jump")
            if not 0 <= instruction.operands[0].imm < len(code):
                raise ValueError("Mapper candidate branches outside its function")
        if "pc" in instruction.op_str:
            raise ValueError("Mapper candidate has a PC-relative operand")


class MapperRunner(Runner):
    """Runner variant that also records reads from the original lookup table."""
    def __init__(self, image: bytes, entry: int, table_address: int, replacement=None):
        self.table_address = table_address
        self.table_reads: set[int] = set()
        super().__init__(image, entry, replacement, replacement_validator=validate_mapper_blob)

    def _memory(self, uc, access, address, size, value, _):
        super()._memory(uc, access, address, size, value, _)
        if access == unicorn.UC_MEM_READ:
            self.table_reads.update(byte for byte in range(address, address + size)
                                    if self.table_address <= byte < self.table_address + 11)

    def run(self, *args, **kwargs):
        self.table_reads.clear()
        return super().run(*args, **kwargs)


def expected_index(value: int, values: tuple[int, ...]) -> int:
    for index, boundary in enumerate(values):
        if value <= boundary:
            return index
    return 0


def make_case(value: int, rng: random.Random, label: str) -> Case:
    regs = tuple(rng.getrandbits(32) for _ in range(13))
    regs = (value,) + regs[1:]
    return Case(label, regs, rng.randbytes(0x1000), rng.randbytes(0x2000),
                rng.getrandbits(4) << 28)


def mapper_access_violation(original_table_reads: set[int] | frozenset[int],
                            candidate_table_reads: set[int] | frozenset[int],
                            original_writes: set[int] | frozenset[int],
                            candidate_writes: set[int] | frozenset[int]) -> dict | None:
    """Reject any data/stack write; original and candidate table reads may differ."""
    # These read sets are intentionally accepted as arguments for an explicit
    # contract boundary. They are recorded for evidence but are not compared.
    _ = original_table_reads, candidate_table_reads
    if original_writes:
        return {"side": "original", "addresses": [hex(x) for x in sorted(original_writes)]}
    if candidate_writes:
        return {"side": "candidate", "addresses": [hex(x) for x in sorted(candidate_writes)]}
    return None


def execute_pair(image: bytes, address: int, code: bytes, values: tuple[int, ...],
                 table_address: int, seed: int, samples: int) -> dict:
    rng = random.Random(seed ^ address)
    original = MapperRunner(image, address, table_address)
    rebuilt = MapperRunner(image, address, table_address, code)
    cases = [(f"byte-{value}", value) for value in range(256)]
    cases += [(f"seeded-{i}", rng.randrange(256)) for i in range(samples)]
    original_table_reads: set[int] = set()
    candidate_table_reads: set[int] = set()
    original_writes: set[int] = set()
    candidate_writes: set[int] = set()
    for label, value in cases:
        case = make_case(value, rng, label)
        left, right = original.run(case), rebuilt.run(case)
        original_table_reads.update(original.table_reads)
        candidate_table_reads.update(rebuilt.table_reads)
        original_writes.update(original.writes)
        candidate_writes.update(rebuilt.writes)
        if left.fault or right.fault or not left.stopped or not right.stopped:
            return {"passed": False, "cases": len(cases), "checked": cases.index((label, value)) + 1,
                    "first_counterexample": {"label": label, "input": value,
                                             "original_fault": left.fault, "candidate_fault": right.fault,
                                             "original_stopped": left.stopped, "candidate_stopped": right.stopped}}
        write_violation = mapper_access_violation(original.table_reads, rebuilt.table_reads,
                                                  original.writes, rebuilt.writes)
        if write_violation:
            return {"passed": False, "cases": len(cases), "checked": cases.index((label, value)) + 1,
                    "first_counterexample": {"label": label, "input": value,
                                             "reason": "mapper contract forbids data/stack writes",
                                             "write_violation": write_violation}}
        if left.result != right.result or left.result != expected_index(value, values):
            return {"passed": False, "cases": len(cases), "checked": cases.index((label, value)) + 1,
                    "first_counterexample": {"label": label, "input": value,
                                             "original_result": left.result, "candidate_result": right.result,
                                             "table_expected": expected_index(value, values)}}
        if left.preserved != left.expected_preserved or right.preserved != right.expected_preserved:
            return {"passed": False, "cases": len(cases), "checked": cases.index((label, value)) + 1,
                    "first_counterexample": {"label": label, "input": value,
                                             "reason": "callee-saved register/SP/VFP contract violated"}}
        if left.data != right.data or left.live_stack != right.live_stack:
            return {"passed": False, "cases": len(cases), "checked": cases.index((label, value)) + 1,
                    "first_counterexample": {"label": label, "input": value, "reason": "memory changed"}}
    return {"passed": True, "cases": len(cases), "exhaustive_byte_cases": 256,
            "seeded_byte_cases": samples, "first_counterexample": None,
            "observed_accesses": {"original_table_read_addresses": [hex(x) for x in sorted(original_table_reads)],
                                  "candidate_table_read_addresses": [hex(x) for x in sorted(candidate_table_reads)],
                                  "original_data_or_stack_write_addresses": [hex(x) for x in sorted(original_writes)],
                                  "candidate_data_or_stack_write_addresses": [hex(x) for x in sorted(candidate_writes)]}}


def experiment(code_path: Path, output: Path, seed: int, samples: int) -> dict:
    started = time.perf_counter()
    output.mkdir(parents=True, exist_ok=False)
    image = code_path.read_bytes()
    code_hash = hashlib.sha256(image).hexdigest()
    game = json.loads((ROOT / "config/game_info.json").read_text(encoding="utf-8"))
    if len(image) != game["code_bin_size"] or code_hash != game["code_sha256"]:
        raise ValueError("Private code.bin does not match configured original revision")
    source_hash = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    obj = output / "h2_config_mapper_candidates.o"
    build = compile_tu_armv6k(SOURCE, obj, ROOT)
    if build.returncode:
        raise RuntimeError(build.stderr)
    symbols = extract_elf_functions_detailed(obj)
    compiled = {}
    for name, (blob, relocations) in symbols.items():
        if name not in {value[0] for value in MAPPERS.values()} | {WRONG}:
            continue
        if relocations:
            raise ValueError(f"Unexpected relocation in {name}: {relocations}")
        compiled[name] = blob
        validate_mapper_blob(blob)
    missing = ({value[0] for value in MAPPERS.values()} | {WRONG}) - compiled.keys()
    if missing:
        raise ValueError(f"Missing compiled mapper symbols: {sorted(missing)}")

    results = []
    for address, (symbol, values) in MAPPERS.items():
        table_address = {0x002CAB70: 0x004077EB, 0x0021F39C: 0x004077F6,
                         0x002E0AF4: 0x00407801}[address]
        result = execute_pair(image, address, compiled[symbol], values, table_address, seed, samples)
        results.append({"address": hex(address), "symbol": symbol,
                        "table_address": {0x002CAB70: "0x004077EB", 0x0021F39C: "0x004077F6",
                                          0x002E0AF4: "0x00407801"}[address],
                        "table_values": values, "compiled_bytes": len(compiled[symbol]), **result})

    control_case = make_case(11, random.Random(seed ^ 0xC0FFEE), "wrong-map-at-11")
    control_original = Runner(image, 0x002CAB70)
    control_rebuilt = Runner(image, 0x002CAB70, compiled[WRONG],
                             replacement_validator=validate_mapper_blob)
    good = control_original.run(control_case)
    bad = control_rebuilt.run(control_case)
    control = {"name": "wrong A threshold 10 changed to 11", "input": 11,
               "original_result": good.result, "wrong_candidate_result": bad.result,
               "detected": good.result != bad.result and good.result == 2 and bad.result == 1,
               "expected_difference": "return value differs"}
    if hashlib.sha256(SOURCE.read_bytes()).hexdigest() != source_hash:
        raise RuntimeError("Candidate source changed during experiment")
    compiler = subprocess.run([str(find_clang()), "--version"], capture_output=True,
                              text=True, check=True).stdout.splitlines()[0]
    passed = all(r["passed"] for r in results) and control["detected"]
    report = {
        "schema": 1, "passed": passed, "scope": "Three titleConfig byte-to-index functions only",
        "reference_sha256": code_hash, "reference_bytes": len(image),
        "source_sha256": source_hash, "object_sha256": hashlib.sha256(obj.read_bytes()).hexdigest(),
        "compiler": compiler, "compile_command": build.args, "compile_exit": build.returncode,
        "seed": seed, "seeded_cases_per_mapper": samples, "random_input_domain": "u8",
        "functions": results, "negative_control": control,
        "evidence": {"compiled": "passed", "arm_differential": "passed" if passed else "failed",
                     "caller": "not_run", "runtime": "not_run"},
        "limitations": [
            "Exhaustively covers valid zero-extended byte arguments (0..255) and seeded duplicate byte cases.",
            "Raw calls with r0 outside 0..255 are outside the titleConfig caller contract.",
            "The runner compares return values, callee-saved registers, SP, d8-d15, and data/stack memory; read footprints differ because the readable candidates encode their thresholds directly.",
            "No caller window, full initializer, game runtime, persistence path, or whole-game behavior was tested.",
            "The source tables were observed in the pinned original code image; the extra adjacent fourth table is outside these function references.",
        ],
        "elapsed_seconds": round(time.perf_counter() - started, 3),
    }
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"passed": passed, "report": str(output / "report.json"),
                      "functions": results, "negative_control": control}, indent=2))
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code", type=Path, default=CODE_DEFAULT)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--samples", type=int, default=256)
    args = parser.parse_args()
    report = experiment(args.code, args.output, args.seed, args.samples)
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
