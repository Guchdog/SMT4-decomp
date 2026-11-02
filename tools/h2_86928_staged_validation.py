#!/usr/bin/env python3
"""Run original-versus-production-staged offline cases for 0x00286928."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import h2_86928_experiment as experiment

BASE = ROOT / "extracted/exefs/code.bin"
STAGED_DIR = ROOT / "build/h2-86928-integration/staged-image"
STAGED = STAGED_DIR / "code.h2-86928.bin"
MANIFEST = STAGED_DIR / "manifest.json"
OUT = ROOT / "build/h2-86928-integration/staged-validation"


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
    original = BASE.read_bytes()
    staged = STAGED.read_bytes()
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if sha(original) != experiment.IMAGE_SHA or sha(staged) != manifest["patched_image_sha256"]:
        raise SystemExit("image hash does not match the pinned base/staged manifest")
    OUT.mkdir(parents=True, exist_ok=True)
    direct = experiment.directed_cases()
    for index, case in enumerate(direct):
        left = experiment.run(case, image=original)
        right = experiment.run(case, image=staged)
        if left != right:
            raise AssertionError(f"production staged direct mismatch {index}: {case}")
    callbacks = callback_cases()
    for index, (case, first_getter) in enumerate(callbacks):
        left = experiment.run(case, callback=True, callback_first_result=first_getter, image=original)
        right = experiment.run(case, callback=True, callback_first_result=first_getter, image=staged)
        if left != right:
            raise AssertionError(f"production staged callback mismatch {index}: {case}")
        helper = next(event for event in right[3] if event[0] == experiment.ENTRY)
        if helper[1] != (0x12003456, 0x87654321, case.incoming_r2, 6) or helper[2] != (1, 0):
            raise AssertionError(f"staged callback ABI mismatch: {helper}")

    report = {
        "schema_version": 1,
        "function": "0x00286928",
        "original_image_sha256": sha(original),
        "staged_image_sha256": sha(staged),
        "production_source_sha256": sha((ROOT / "src/engine/leaf_batch45_a.cpp").read_bytes()),
        "production_object_sha256": manifest["object_sha256"],
        "candidate_body_bytes": manifest["compiled_body_bytes"],
        "slot_bytes": manifest["slot_bytes"],
        "direct_cases": len(direct),
        "callback_cases": len(callbacks),
        "callback": "original pinned 0x00221168; synthetic upstream getter returns; production helper installed only in staged image",
        "result": "passed",
        "limitations": [
            "All helper direct callees and callback getters remain stubbed as in the differential fixture.",
            "The callback's handler 0x001A07CC continuation and emulator runtime are not covered."
        ]
    }
    report_path = OUT / "production-offline-validation.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    manifest["evidence"]["arm_differential"] = "passed"
    manifest["evidence"]["caller"] = "passed: 296 direct plus 4 callback compositions, stub-scoped"
    manifest["staged_validation_report"] = str(report_path.relative_to(ROOT))
    manifest["staged_validation_sha256"] = sha(report_path.read_bytes())
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"PASS staged production image: {len(direct)} direct + {len(callbacks)} callback cases")
    print(f"REPORT {report_path.relative_to(ROOT)} SHA256 {sha(report_path.read_bytes())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
