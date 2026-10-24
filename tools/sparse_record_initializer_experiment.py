#!/usr/bin/env python3
"""Two-seed differential for the sparse ordinary-memory initializer at 0x00140854."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import random
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import capstone
from tools.semantic_experiment import DATA, DATA_SIZE, STACK_SIZE, TEXT, Case, Runner
from tools.semantic_experiment_support import compile_candidate_symbols, load_pinned_reference

ADDRESS = 0x00140854
SIZE = 88
SOURCE = ROOT / "experiments/semantic_equivalence/sparse_record_initializer_candidate.cpp"
SEEDS = (7, 20261024)
EXPECTED = (
    ("mov", "r2, #0"), ("str", "r2, [r0, #4]"), ("strh", "r2, [r0, #8]"),
    ("str", "r2, [r0, #0xc]"), ("strh", "r2, [r0, #0x10]"),
    ("str", "r2, [r0, #0x14]"), ("add", "r1, r0, #0x18"), ("mvn", "ip, #0"),
    ("stm", "r1, {r2, ip}"), ("str", "r2, [r0, #0x2c]"),
    ("str", "r2, [r0, #0x30]"), ("str", "r2, [r0, #0xb8]"),
    ("strh", "r2, [r0, #0xbc]"), ("str", "r2, [r0, #0xc0]"),
    ("strh", "r2, [r0, #0xc4]"), ("str", "r2, [r0, #0xc8]"),
    ("add", "r3, r0, #0xcc"), ("stm", "r3, {r2, ip}"),
    ("str", "r2, [r0, #0xe0]"), ("str", "r2, [r0, #0xe4]"),
    ("strb", "r2, [r0, #0x18d]"), ("bx", "lr"),
)


def verify_reference(image: bytes, game_info: dict, ledger: list[dict]) -> dict:
    digest = hashlib.sha256(image).hexdigest()
    if digest != game_info["code_sha256"]:
        raise ValueError("code.bin SHA-256 differs from configured pin")
    row = next((item for item in ledger if int(item["address"], 16) == ADDRESS), None)
    if row is None or row["status"].strip() != "matching" or int(row["size"]) != SIZE:
        raise ValueError("missing matching 88-byte row at 0x00140854")
    start = ADDRESS - TEXT
    body = image[start:start + SIZE]
    decoder = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    actual = tuple((insn.mnemonic.lower(), insn.op_str.lower())
                   for insn in decoder.disasm(body, ADDRESS))
    if actual != EXPECTED:
        raise ValueError(f"reference instructions changed: {actual}")
    return {"code_sha256": digest, "functions": {hex(ADDRESS): {
        "name": row["name"], "size": SIZE, "sha256": hashlib.sha256(body).hexdigest(),
        "bytes": body.hex(),
        "semantics": "Writes a fixed sparse pattern of zero words/halfwords/byte and all-ones words through offset 0x18d; no reads; leaves r0 unchanged.",
    }}}


def _case(seed: int, index: int, record_offset: int) -> Case:
    rng = random.Random(seed ^ (index * 0x9E3779B1))
    data = bytearray(rng.randbytes(DATA_SIZE))
    regs = [rng.getrandbits(32) for _ in range(13)]
    regs[0] = DATA + record_offset
    return Case(f"case-{index}", tuple(regs), bytes(data), rng.randbytes(STACK_SIZE),
                (0, 0x40000000, 0x80000000, 0xC0000000)[index % 4])


def _compare(original, candidate) -> str | None:
    if bool(original.fault) != bool(candidate.fault):
        return "fault outcome differs"
    if original.preserved != candidate.preserved:
        return "callee-saved state differs"
    if original.data != candidate.data:
        return "memory differs"
    if original.reads != candidate.reads or original.writes != candidate.writes:
        return "access footprint differs"
    if not original.fault and (not original.stopped or not candidate.stopped):
        return "normal return not observed"
    if not original.fault and (original.result != candidate.result or original.pc != candidate.pc):
        return "return continuation differs"
    return None


def run(code_path: Path, output: Path, seed: int) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    pinned = load_pinned_reference(code_path, ROOT / "config/game_info.json",
                                   ROOT / "config/functions.csv")
    reference = verify_reference(pinned.image, pinned.game_info, pinned.ledger)
    symbols = compile_candidate_symbols(
        SOURCE, output / "sparse_record_initializer.o", ROOT,
        {"candidate_00140854", "negative_wrong_record_sentinel", "negative_omit_record_tail"})
    original = Runner(pinned.image, ADDRESS)
    candidate = Runner(pinned.image, ADDRESS, symbols["candidate_00140854"])
    cases = [(0x300 + 4 * (index % 12)) for index in range(64)]
    cases.append(DATA_SIZE - 0x18D)
    failure = None
    fault_cases = 0
    for index, record_offset in enumerate(cases):
        case = _case(seed, index, record_offset)
        ref, rebuilt = original.run(case), candidate.run(case)
        fault_cases += int(bool(ref.fault))
        reason = _compare(ref, rebuilt)
        if reason:
            failure = {"case": case.label, "reason": reason,
                       "original_fault": ref.fault, "candidate_fault": rebuilt.fault}
            break
    result = {"address": hex(ADDRESS), "candidate_bytes": len(symbols["candidate_00140854"]),
              "cases": len(cases) if failure is None else index + 1,
              "fault_cases": fault_cases, "passed": failure is None, "failure": failure}
    control_case = _case(seed + 101, 80, 0x500)
    base = Runner(pinned.image, ADDRESS).run(control_case)
    controls = []
    for symbol in ("negative_wrong_record_sentinel", "negative_omit_record_tail"):
        wrong = Runner(pinned.image, ADDRESS, symbols[symbol]).run(control_case)
        controls.append({"candidate": symbol, "detected": base.data != wrong.data or base.writes != wrong.writes})
    report = {
        "schema": 1, "experiment": "sparse_record_initializer_00140854",
        "passed": result["passed"] and all(item["detected"] for item in controls),
        "scope": "one pinned ordinary-memory ARM leaf; isolated differential, not game boot",
        "reference_sha256": pinned.game_info["code_sha256"],
        "reference_functions": reference["functions"],
        "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "seed": seed, "function_comparisons": result["cases"],
        "case_mix": {"randomized_records": 64, "final_byte_fault": 1},
        "functions": [result], "negative_controls": controls, "caller_windows": [],
        "limitations": ["Finite seeded cases do not prove behavior for every possible caller object.",
                        "Only ordinary RAM and isolated ARM11 execution were tested.",
                        "The caller's full allocation size and semantics are not inferred."],
    }
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report
