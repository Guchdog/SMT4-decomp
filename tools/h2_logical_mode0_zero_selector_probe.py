#!/usr/bin/env python3
"""Check selector-zero behavior of the H2 mode-0 query against pinned ARM."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import h2_logical_mode0_query_experiment as query

IMAGE_SHA = "1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def run(out: Path) -> dict:
    out.mkdir(parents=True, exist_ok=False)
    image = query.CODE_DEFAULT.read_bytes()
    if sha(image) != IMAGE_SHA:
        raise ValueError("pinned ARM image hash mismatch")
    code, obj, compiler_args = query.compile_symbols(out / "compile")
    original, _, original_calls = query.machine(image)
    candidate, _, candidate_calls = query.machine(image, code["good"])
    cases = [
        (0, 0, 2, 0, 0),
        (4, 0, 8, 7, 0),
        (30, 0, 0xFFFFFFFF, 0x80000000, 0),
        (4, 0, 1, 0, 0),
        (4, 1, 8, 7, 0),
        (31, 0, 8, 7, 0),
        (4, 0, 8, 8, 0),
    ]
    rows = []
    for index, (query_id, flags, counter, threshold, selector) in enumerate(cases):
        ref = query.invoke_recorded(original, query.ADDRESS, query_id, flags,
                                    counter, threshold, selector, index + 1,
                                    helper_calls=original_calls)
        got = query.invoke_recorded(candidate, query.INJECT, query_id, flags,
                                    counter, threshold, selector, index + 1,
                                    helper_calls=candidate_calls)
        mismatch = query.compare(ref, got)
        expected_calls = query.helper_arguments_expected(query_id, flags, counter, threshold, selector)
        if not mismatch and ref["division_helper_trace"] != expected_calls:
            mismatch = "helper arguments differ from unsigned query contract"
        if query_id < 31 and (flags & 1) == 0 and counter == 1:
            expected = 1
        elif query_id >= 31 or (flags & 1) != 0 or counter <= threshold:
            expected = 0
        elif selector == 0:
            expected = 0  # original unsigned helper returns remainder=dividend
        else:
            expected = int((counter - threshold) % selector == 0)
        if ref["return"] != expected:
            mismatch = f"pinned return {ref['return']} != expected {expected}"
        rows.append({"inputs": [query_id, flags, counter, threshold, selector],
                     "expected_return": expected, "original": ref, "candidate": got,
                     "result": "passed" if mismatch is None else "failed",
                     "mismatch": mismatch})
        if mismatch:
            raise AssertionError(json.dumps(rows[-1], indent=2))
    report = {
        "schema_version": 1, "image_sha256": sha(image),
        "source_sha256": sha(query.SOURCE.read_bytes()), "runner_dependency_sha256": sha(Path(__file__).read_bytes()),
        "candidate_object_sha256": sha(obj.read_bytes()), "compiler_args": compiler_args,
        "cases": len(rows), "selector_zero_cases": sum(row["inputs"][4] == 0 for row in rows),
        "cases_include": ["eligible positive dividend", "high unsigned dividend", "pulse bypass",
                          "availability bypass", "invalid ID bypass", "threshold bypass"],
        "rows": rows, "all_passed": True,
        "limits": ["mode-0 wrapper calls the pinned original unsigned service; this does not reconstruct 0x002C6C10",
                   "controlled globals/counters only; no input producer, scheduler, or runtime claim"]}
    path = out / "report.json"
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"all_passed": True, "cases": len(rows), "report": str(path),
                      "sha256": sha(path.read_bytes())}, indent=2))
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    run(args.out.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
