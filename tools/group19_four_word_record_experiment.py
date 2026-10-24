#!/usr/bin/env python3
"""Run group #19's three four-word record writers with two independent seeds."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.aoc_initializer_experiment import run as run_initializer_experiment


DEFAULT_SEEDS = (20261024, 7)


def run(code_path: Path, output: Path, seeds: tuple[int, ...] = DEFAULT_SEEDS,
        samples: int = 64) -> dict:
    """Execute the pinned differential harness once per distinct seed."""
    if len(seeds) < 2 or len(set(seeds)) != len(seeds):
        raise ValueError("provide at least two distinct random seeds")
    if samples < 0:
        raise ValueError("samples must be non-negative")

    output.mkdir(parents=True, exist_ok=True)
    runs = []
    for seed in seeds:
        run_report = run_initializer_experiment(
            code_path, output / f"seed-{seed}", seed=seed, samples=samples
        )
        runs.append(run_report)

    addresses = runs[0]["candidate_functions"]
    per_function = []
    for initial in addresses:
        address = initial["address"]
        matching = [next(item for item in report["candidate_functions"]
                         if item["address"] == address) for report in runs]
        per_function.append({
            "address": address,
            "candidate": initial["candidate"],
            "passed_all_seeds": all(item["passed"] for item in matching),
            "case_counts": [item["case_count"] for item in matching],
            "byte_identical": all(item["byte_identical"] for item in matching),
        })

    summary = {
        "schema": 1,
        "family": "group #19 four-word record writers",
        "passed": all(report["passed"] for report in runs)
        and all(item["passed_all_seeds"] for item in per_function),
        "seeds": list(seeds),
        "random_samples_per_function_per_seed": samples,
        "functions": per_function,
        "runs": runs,
        "limitations": [
            "This is bounded isolated ARM differential evidence, not a formal proof",
            "Caller snippets are statically verified; no live game caller was run",
            "The VM descriptor's semantic type name remains unknown",
            "No production source, ledger, ROM, IPS, emulator, or save was modified",
        ],
    }
    summary_path = output / "group19_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"Group #19 record experiment {'PASS' if summary['passed'] else 'FAIL'}; "
          f"summary: {summary_path}")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code", type=Path, default=ROOT / "extracted/exefs/code.bin")
    parser.add_argument("--output", type=Path,
                        default=ROOT / "build/semantic-equivalence/group19-records")
    parser.add_argument("--seeds", type=int, nargs="+", default=list(DEFAULT_SEEDS))
    parser.add_argument("--samples", type=int, default=64)
    args = parser.parse_args()
    try:
        report = run(args.code, args.output, tuple(args.seeds), args.samples)
    except (RuntimeError, ValueError, OSError) as error:
        parser.exit(2, f"Experiment error: {error}\n")
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
