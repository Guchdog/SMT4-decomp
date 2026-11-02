#!/usr/bin/env python3
"""Compare run-013 and two-slot touch-region images through original memory fixtures."""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import struct
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools import h2_b88c4_experiment as experiment


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def compact(value: dict) -> dict:
    return {k: (sha(v) if k == "records" else v) for k, v in value.items()}


def run(base_path: Path, staged_path: Path, manifest_path: Path, output: Path, seed: int) -> dict:
    base, staged = base_path.read_bytes(), staged_path.read_bytes()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if sha(base) != manifest["base_image_sha256"] or sha(staged) != manifest["patched_image_sha256"]:
        raise ValueError("image hash differs from staging manifest")
    if len(base) != len(staged) or not manifest["only_declared_slots_changed"]:
        raise ValueError("image length or declared slot scope invalid")
    base_profile, staged_profile = experiment.setup(image=base), experiment.setup(image=staged)
    counts = (0, 1, 37, 199, 200)
    cases = [(count, custom, seed + i) for i, (count, custom) in enumerate(
        (pair for count in counts for pair in ((count, False), (count, True))))]
    rng = random.Random(seed ^ 0xBF6D088C4)
    cases.extend((rng.randrange(0, 200), bool(i & 1), rng.getrandbits(32)) for i in range(48))
    mismatches = []
    for i, (count, custom, case_seed) in enumerate(cases):
        ref, _ = experiment.execute(base_profile, experiment.CALLER, count, custom, case_seed)
        got, _ = experiment.execute(staged_profile, experiment.CALLER, count, custom, case_seed)
        # The called original divider in the typed resolver may leave temporary
        # spill bytes below SP; exclude them while retaining caller-visible writes.
        for result in (ref, got):
            result["external_writes"] = [w for w in result["external_writes"]
                                         if not experiment.STACK - 0x100 <= w[0] < experiment.STACK]
        if ref != got:
            mismatches.append({"case": i, "count": count, "custom": custom,
                               "seed": case_seed, "base": compact(ref), "staged": compact(got)})
            break
    # Independently verify exact patch footprint against the two declared slots.
    changed = {i for i, (a, b) in enumerate(zip(base, staged)) if a != b}
    allowed = set()
    for slot in manifest["slots"]:
        start = int(slot["address"], 16) - 0x00100000
        allowed.update(range(start, start + slot["span"]))
    if not changed <= allowed:
        raise AssertionError(f"staged image changes undeclared offset {min(changed - allowed):#x}")
    output.mkdir(parents=True, exist_ok=False)
    report = {
        "schema_version": 1, "base_sha256": sha(base), "staged_sha256": sha(staged),
        "manifest_sha256": sha(manifest_path.read_bytes()), "seed": seed,
        "cases": len(cases), "directed_counts": list(counts), "custom_and_inline_region_forms": True,
        "seeded_cases": 48, "changed_bytes": len(changed), "changed_bytes_within_two_slots": True,
        "caller_chain": "original entry 0x002B88C4 executes staged typed 0x002B88C4 and staged typed 0x002BF6D0; original manager resolver 0x002B0188 and divider 0x002C615C execute",
        "checks": "return, records, count, ordered non-stack writes, both resolver argument pairs, callee-saved registers, SP, completion and faults",
        "below_sp_residue": "excluded through STACK-0x100; restored SP and caller-visible outputs compared",
        "result": "passed" if not mismatches else "failed", "mismatches": mismatches,
        "runtime": "not_run",
        "limits": ["valid controlled manager/table/node/touch fixtures only", "runtime scheduler and manager lifetime untested"]}
    path = output / "report.json"
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    print(f"REPORT {path.relative_to(ROOT)} SHA256 {sha(path.read_bytes())}")
    if mismatches:
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--staged", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=20261118)
    args = parser.parse_args()
    return run(args.base.resolve(), args.staged.resolve(), args.manifest.resolve(), args.out.resolve(), args.seed)


if __name__ == "__main__":
    raise SystemExit(main())
