#!/usr/bin/env python3
"""Run the in-place candidate through the original ARM call and fallthrough sites."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tools.h2_apt_utility4_inplace_experiment import run_experiment


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--code", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--base-image", type=Path)
    parser.add_argument("--base-sha256")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    passed = run_experiment(args.code, args.output / "composition",
                            args.base_image, args.base_sha256)
    report = json.loads((args.output / "composition" / "report.json").read_text(encoding="utf-8"))
    caller_starts = {hex(address) for address in
                     (0x002C0F6C, 0x002C1260, 0x002C1304, 0x00106F00,
                      0x0010700C, 0x002A8164, 0x002C5638, 0x002C0EE0)}
    summary = {"passed": passed,
               "caller_counts": {key: value for key, value in report["caller_counts"].items()
                                 if key in caller_starts},
               "source_report": str(args.output / "composition" / "report.json"),
               "limitations": report["limits"]}
    (args.output / "caller-composition.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
