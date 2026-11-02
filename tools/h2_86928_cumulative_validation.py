#!/usr/bin/env python3
"""Offline-validate the 0x00286928 delta on the prior cumulative H2 image."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import h2_86928_experiment as experiment

BASE = ROOT / "build/h2-8d24-integration/runtime-image/code.h2-runtime.bin"
FINAL = ROOT / "build/h2-86928-integration/cumulative-image/code.h2-86928-runtime.bin"
MANIFEST = FINAL.with_name("manifest.json")
OUT = ROOT / "build/h2-86928-integration/cumulative-validation"
ENTRY = 0x00286928
SPAN = 820


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def callback_cases():
    cases = []
    for seed in (17, 4729):
        cases.append((experiment.Case(seed, 6, 0, 1, state_2e=0, state_35=1,
                                      row=8, arg5=0, arg6=0), 0))
        cases.append((experiment.Case(seed, 6, 1, 4, state_2e=0, state_35=1,
                                      row=8, arg5=0, arg6=0), 1))
    return cases


def main() -> int:
    base, final = BASE.read_bytes(), FINAL.read_bytes()
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if sha(base) != manifest["base_sha256"] or sha(final) != manifest["patched_sha256"]:
        raise SystemExit("cumulative image does not match its pinned manifest")
    offset = ENTRY - experiment.TEXT
    if final[:offset] != base[:offset] or final[offset + SPAN:] != base[offset + SPAN:]:
        raise SystemExit("cumulative comparison base differs outside 0x00286928")
    OUT.mkdir(parents=True, exist_ok=True)
    cases = experiment.directed_cases()
    for index, case in enumerate(cases):
        if experiment.run(case, image=base) != experiment.run(case, image=final):
            raise AssertionError(f"cumulative direct mismatch {index}: {case}")
    callbacks = callback_cases()
    for index, (case, first_getter) in enumerate(callbacks):
        before = experiment.run(case, callback=True, callback_first_result=first_getter, image=base)
        after = experiment.run(case, callback=True, callback_first_result=first_getter, image=final)
        if before != after:
            raise AssertionError(f"cumulative callback mismatch {index}: {case}")

    report = {
        "schema_version": 1,
        "base_image_sha256": sha(base), "cumulative_image_sha256": sha(final),
        "direct_cases": len(cases), "callback_cases": len(callbacks),
        "only_new_slot_differs_from_base": True, "result": "passed",
        "scope": "fixed-stub direct dependencies; original 0x00221168 callback; synthetic getters",
        "limitations": ["No original dependency bodies, 0x001A07CC handler continuation, or emulator runtime."]
    }
    report_path = OUT / "cumulative-offline-validation.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"PASS cumulative H2 delta: {len(cases)} direct + {len(callbacks)} callback cases")
    print(f"REPORT {report_path.relative_to(ROOT)} SHA256 {sha(report_path.read_bytes())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
