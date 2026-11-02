"""Build an in-place IPS and compare the composed accumulated H2 cursor path."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.h2_calc_code_patch import apply_ips, encode_ips, sha256
from tools.h2_1ff3c4_experiment import ENTRY, IMAGE, SPAN, TEXT_BASE, candidate_body
from tools import h2_29f278_slot_experiment as slot
from tools import h2_calc_experiment as calc

ACCUMULATED = ROOT / "build/agent-work/H2-semantic/h2-titleconfig-0029f278-slot/run004/code.h2-cursor.bin"
ACCUMULATED_SHA = "d16516c9ce191d88f728d14dcc08bf4bf2a6d3a81ee11603f4b00253e8b1c9cb"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    if args.output.exists():
        raise FileExistsError(f"refusing to reuse output directory: {args.output}")
    args.output.mkdir(parents=True)
    base = ACCUMULATED.read_bytes()
    if sha256(base) != ACCUMULATED_SHA:
        raise ValueError("pinned accumulated H2+0x0029F278 base hash mismatch")
    body, relocs = candidate_body()
    if len(body) != 880 or ENTRY & 3 or len(body) > SPAN:
        raise ValueError("unexpected axis candidate placement/size")
    offset = ENTRY - TEXT_BASE
    final = bytearray(base)
    final[offset:offset + len(body)] = body
    if final[offset + len(body):offset + SPAN] != base[offset + len(body):offset + SPAN]:
        raise ValueError("the original slot suffix was not preserved")
    patch = encode_ips([(offset, body)], len(base))
    if apply_ips(base, patch) != bytes(final):
        raise ValueError("IPS roundtrip did not reconstruct the in-place image")
    output_image = args.output / "code.h2-cursor-axis.bin"
    output_ips = args.output / "code.h2-cursor-axis.ips"
    output_image.write_bytes(final)
    output_ips.write_bytes(patch)

    scenarios = [
        ("stable-cursor", calc.Scenario("cursor-stable", 1, row=1),
         dict(first_threshold=1, second_threshold=1, first_base=1, second_base=1,
              total=3, input_state=0, counts={})),
        ("active-cursor-no-input", calc.Scenario("cursor-active", 1, row=1),
         dict(first_threshold=2, second_threshold=2, first_base=1, second_base=1,
              total=3, input_state=0, counts={})),
        ("logical-bits", calc.Scenario("cursor-bits", 1, row=1),
         dict(first_threshold=1, second_threshold=1, first_base=1, second_base=1,
              total=3, input_state=0x1F8, counts={})),
        ("h2-initialized-cursor", calc.Scenario("cursor-h2-setup", 1, row=1),
         dict(first_threshold=3, second_threshold=1, first_width=3, second_width=1,
              first_start=2, first_count=3, second_count=1, first_flags=6,
              second_flags=6, first_base=0, second_base=0, total=3,
              first_ids=(6, 5, 0x20, 0x20, 15, 14, 0x20, 0x20),
              second_ids=(3, 4, 0x20, 0x20, 12, 13, 0x20, 0x20),
              input_state=0, counts={})),
    ]
    rows = []
    for label, scenario, cursor in scenarios:
        left = slot.CalcWithActualCursor(base, scenario=scenario)
        right = slot.CalcWithActualCursor(bytes(final), scenario=scenario)
        left.initialize_cursor(**cursor)
        right.initialize_cursor(**cursor)
        original, candidate = left.run(), right.run()
        error = calc.compare(original, candidate)
        rows.append({"label": label, "passed": error is None, "error": error,
                     "original_return": hex(original["return"]),
                     "trace_count": len(original["trace"])})
    report = {
        "base_sha256": sha256(base), "result_sha256": sha256(final),
        "ips_sha256": sha256(patch),
        "candidate_body_bytes": len(body), "candidate_body_sha256": sha256(body),
        "relocations": relocs, "suffix_preserved": True,
        "title_calc_compositions": rows,
    }
    # Bind the source and runner inputs explicitly in the report.
    report["source_sha256"] = sha256((ROOT / "src/engine/leaf_batch43_a.cpp").read_bytes())
    report["runner_sha256"] = sha256((ROOT / "tools/h2_1ff3c4_integrate.py").read_bytes())
    report["differential_runner_sha256"] = sha256((ROOT / "tools/h2_1ff3c4_experiment.py").read_bytes())
    (args.output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"base_sha256": report["base_sha256"], "result_sha256": report["result_sha256"],
                      "ips_sha256": report["ips_sha256"], "compositions": rows}, indent=2))
    return 1 if any(not row["passed"] for row in rows) else 0


if __name__ == "__main__":
    raise SystemExit(main())
