#!/usr/bin/env python3
"""Compare run-013 base and staged H2 images through the touch caller chain."""
from __future__ import annotations

import hashlib
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import h2_b88c4_experiment as experiment

BASE = ROOT / "build/agent-work/H2-semantic/h2-init-ready-final-image/run-013/combined-build-final/code.combined.bin"
MANIFEST = ROOT / "build/agent-work/H2-semantic/h2-helper-002b88c4-staged-integration/run001/staging/manifest.json"
STAGED = ROOT / "build/agent-work/H2-semantic/h2-helper-002b88c4-staged-integration/run001/staging/code.h2-touch-region.bin"
OUT = ROOT / "build/agent-work/H2-semantic/h2-helper-002b88c4-staged-integration/run001/validation"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    base, staged = BASE.read_bytes(), STAGED.read_bytes()
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if sha(base) != manifest["base_image_sha256"] or sha(staged) != manifest["patched_image_sha256"]:
        raise SystemExit("base/staged image hash differs from manifest")
    if manifest["original_code_image_sha256"] != experiment.IMAGE_SHA:
        raise SystemExit("staging manifest is based on a different pinned original")
    original = experiment.setup(image=base)
    replacement = experiment.setup(image=staged)
    counts = (0, 1, 37, 199, 200)
    cases = [(count, custom, 0x20261102 + i) for i, (count, custom) in enumerate(
        ((count, custom) for count in counts for custom in (False, True)))]
    rng = random.Random(20261102)
    cases.extend((rng.randrange(0, 200), bool(i & 1), rng.getrandbits(32)) for i in range(48))
    for i, (count, custom, seed) in enumerate(cases):
        ref, _ = experiment.execute(original, experiment.CALLER, count, custom, seed)
        staged_result, _ = experiment.execute(replacement, experiment.CALLER, count, custom, seed)
        if ref != staged_result:
            def compact(value):
                return {k: (sha(v) if k == "records" else v) for k, v in value.items()}
            raise AssertionError(f"staged mismatch case {i}: {compact(ref)} != {compact(staged_result)}")
    OUT.mkdir(parents=True, exist_ok=True)
    manifest["evidence"]["staged_differential"] = "passed: 58/58 original-versus-staged cases"
    manifest["evidence"]["caller"] = "passed: original 0x002BF6D0 and 0x00138B90 execute in the staged caller chain"
    manifest["staged_validation_report"] = str((OUT / "staged-image-validation.json").relative_to(ROOT))
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    report = {
        "schema_version": 1, "function": "0x002B88C4",
        "base_image_sha256": sha(base), "staged_image_sha256": sha(staged),
        "manifest_sha256": sha(MANIFEST.read_bytes()), "candidate_source_sha256": manifest["source_sha256"],
        "candidate_body_sha256": manifest["compiled_body_sha256"], "candidate_body_bytes": manifest["compiled_body_bytes"],
        "cases": len(cases), "counts": list(counts), "custom_and_inline_record_forms": True,
        "seeded_cases": 48, "negative_controls": "covered by tools/h2_b88c4_experiment.py against pinned original",
        "caller_chain": "staged 0x002B88C4 C++; original 0x002BF6D0 and 0x00138B90; original byte-matching 0x002B0188",
        "checks": "return, record bytes, count, ordered memory writes, helper inputs, callee-saved GPRs, SP, completion and faults",
        "result": "passed", "runtime": "not_run",
        "limits": ["Controlled valid manager/table/node/touch fixtures; no natural scheduler lifecycle or real runtime path."],
    }
    path = OUT / "staged-image-validation.json"
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    print(f"REPORT {path.relative_to(ROOT)} SHA256 {sha(path.read_bytes())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
