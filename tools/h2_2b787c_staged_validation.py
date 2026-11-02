#!/usr/bin/env python3
"""Validate 0x002B787C at its final address in the staged production image."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools import h2_2b787c_experiment as experiment

STAGED = ROOT / "build/h2-2b787c-integration/staged-image/code.h2-2b787c.bin"
OUT = ROOT / "build/h2-2b787c-integration/staged-validation"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    original = experiment.IMAGE
    staged = STAGED.read_bytes()
    if len(staged) != len(original):
        raise SystemExit("staged image length differs from pinned original")
    cases = experiment.make_cases()
    for i, case in enumerate(cases):
        before = experiment.run_helper(case, image=original)
        after = experiment.run_helper(case, image=staged)
        if before != after:
            raise AssertionError(f"final-address differential mismatch {i} {case.name}: {before} != {after}")
    caller_rows = []
    for selector in (11, 19):
        before = experiment.run_parent_composition(selector, None, image=original)
        after = experiment.run_parent_composition(selector, None, image=staged)
        if before != after:
            raise AssertionError(f"staged caller mismatch selector {selector}: {before} != {after}")
        if not after["done"] or not after["candidate_hit"] or after["object_20"] != 2:
            raise AssertionError(f"staged caller did not consume line count for selector {selector}: {after}")
        caller_rows.append({"selector": selector, "entry_hit": after["candidate_hit"],
                            "stored_line_count": after["object_20"]})
    report = {
        "function": "AsdText_GetLineCount / 0x002B787C",
        "original_image_sha256": sha(original),
        "staged_image_sha256": sha(staged),
        "staged_function_sha256": sha(staged[0x002B787C - 0x00100000:0x002B787C - 0x00100000 + 176]),
        "direct_cases_compared": len(cases),
        "direct_cases_passed": len(cases),
        "caller_compositions": caller_rows,
        "final_address_execution": True,
        "runtime": "not_run",
        "limits": [
            "The caller fixture uses deterministic hooks for 0x00286928 services other than this helper.",
            "The staged checks use initialized table fixtures with reachable sentinels; malformed and concurrent inputs remain outside the contract.",
            "This is offline instruction-level evidence and does not establish game runtime selector distribution or user-facing text labels.",
        ],
    }
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "production-offline-validation.json"
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"PASS staged direct={len(cases)} caller=2 final-address; report={path}; sha256={sha(path.read_bytes())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
