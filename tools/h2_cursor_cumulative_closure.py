"""Compose the reviewed H2 cursor replacements and run bounded offline callers."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.h2_calc_code_patch import apply_ips, sha256
from tools import h2_29f278_slot_experiment as slot
from tools import h2_calc_experiment as calc
from tools import h2_254ca8_experiment as query

BASE = ROOT / "build/agent-work/H2-semantic/h2-final-image-composition/run-001/composed-003/code.h2-final.bin"
BASE_SHA = "acd8b2f35df08f225ca65b0fbf8aeef2dbbaa71171904e31c301e8bff6a51446"
CURSOR_IMAGE = ROOT / "build/h2-1ff3c4-integrated/run002/code.h2-cursor-axis.bin"
CURSOR_SHA = "37cb6046f1be329d7af06ef36430a52897b49c0f96d5b5fdb4353bef39fd4876"
QUERY_IPS = ROOT / "build/agent-work/H2-semantic/h2-titleconfig-00254ca8-offline-integration/run005/code.production.ips"
QUERY_IPS_SHA = "db23257413866439b86d9ce784da6804b5153106b7386a26356f1751443400ae"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def caller_scenarios():
    return [
        ("stable-cursor", calc.Scenario("cursor-stable", 1, row=1),
         dict(first_threshold=1, second_threshold=1, first_base=1, second_base=1,
              total=3, input_state=0, counts={})),
        ("active-cursor-no-input", calc.Scenario("cursor-active", 1, row=1),
         dict(first_threshold=2, second_threshold=2, first_base=1, second_base=1,
              total=3, input_state=0, counts={})),
        ("logical-input-bits", calc.Scenario("cursor-bits", 1, row=1),
         dict(first_threshold=1, second_threshold=1, first_base=1, second_base=1,
              total=3, input_state=0x1F8, counts={})),
        ("initialized-h2-special-ids", calc.Scenario("cursor-h2-setup", 1, row=1),
         dict(first_threshold=3, second_threshold=1, first_width=3, second_width=1,
              first_start=2, first_count=3, second_count=1, first_flags=6,
              second_flags=6, first_base=0, second_base=0, total=3,
              first_ids=(6, 5, 0x20, 0x20, 15, 14, 0x20, 0x20),
              second_ids=(3, 4, 0x20, 0x20, 12, 13, 0x20, 0x20),
              input_state=0, counts={})),
    ]


def run(out: Path) -> dict:
    if out.exists():
        raise FileExistsError(f"refusing to reuse output directory: {out}")
    out.mkdir(parents=True)
    base = BASE.read_bytes()
    if sha(base) != BASE_SHA:
        raise ValueError("pinned accumulated original H2 base hash mismatch")
    cursor = CURSOR_IMAGE.read_bytes()
    if sha(cursor) != CURSOR_SHA:
        raise ValueError("pinned image with reviewed 0x29F278 and 0x1FF3C4 mismatch")
    query_ips = QUERY_IPS.read_bytes()
    if sha(query_ips) != QUERY_IPS_SHA:
        raise ValueError("pinned reviewed 0x254CA8 IPS mismatch")
    if len(base) != len(cursor):
        raise ValueError("accumulated image size changed")

    # Apply the reviewed query-service slot patch to the already reviewed cursor image.
    cumulative = apply_ips(cursor, query_ips)
    if len(cumulative) != len(base):
        raise ValueError("cumulative image size differs from the pinned base")
    if apply_ips(cursor, query_ips) != cumulative:
        raise ValueError("query IPS composition is not deterministic")
    (out / "code.h2-cursor-cumulative.bin").write_bytes(cumulative)
    (out / "code.h2-cursor-cumulative.ips").write_bytes(
        # IPS is retained byte-for-byte as the final incremental patch. The
        # composition report separately pins the preceding 29F/1FF image.
        query_ips)

    changed = [i for i, (a, b) in enumerate(zip(base, cumulative)) if a != b]
    expected = [(0x0029F278, 0x0029F67C), (0x001FF3C4, 0x001FF734),
                (0x00254CA8, 0x00254F28)]
    # Changed bytes can be sparse within ARM instructions; prove every delta
    # is confined to the three reviewed candidate body extents.
    allowed = [(start - 0x00100000, end - 0x00100000) for start, end in expected]
    outside = [offset for offset in changed
               if not any(start <= offset < end for start, end in allowed)]
    if outside:
        raise ValueError(f"changed bytes escaped candidate extents: {[hex(x + 0x00100000) for x in outside[:12]]}")
    actual = expected

    calc_rows = []
    for label, scenario, cursor_state in caller_scenarios():
        left = slot.CalcWithActualCursor(base, scenario=scenario)
        right = slot.CalcWithActualCursor(cumulative, scenario=scenario)
        left.initialize_cursor(**cursor_state)
        right.initialize_cursor(**cursor_state)
        original, candidate = left.run(), right.run()
        error = calc.compare(original, candidate)
        calc_rows.append({"label": label, "passed": error is None, "error": error,
                          "original_return": hex(original["return"]),
                          "candidate_return": hex(candidate["return"]),
                          "trace_count": len(original["trace"]),
                          "cursor_after": candidate["work"][0xE8:0x14C].hex()})

    # This caller starts at the mover and executes its selected image body plus
    # the selected 0x254CA8 body. Lower logical/axis/angle helpers remain the
    # explicit deterministic service seams from the accepted query harness.
    query_rows = []
    mover_cases = [
        ("initialized-h2-idle", {"mode0_query": {}, "mode1_query": {}, "mask_query": {}}),
        ("initialized-primary-6-special-15", {
            "mode0_query": {"6": 1}, "mode1_query": {"6": 0}, "mask_query": {"15": 1}}),
        ("initialized-primary-6-special-14", {
            "mode0_query": {"6": 1}, "mode1_query": {"6": 0}, "mask_query": {"14": 1}}),
    ]
    for label, by_id in mover_cases:
        original, candidate = query.run_mover(base, by_id), query.run_mover(cumulative, by_id)
        query_rows.append({"label": label, "passed": original == candidate,
                           "original_error": original["error"],
                           "candidate_error": candidate["error"],
                           "original_return": hex(original["ret"]),
                           "candidate_return": hex(candidate["ret"]),
                           "trace_count": len(candidate["trace"]),
                           "trace": candidate["trace"],
                           "cursor": candidate["cursor"]})

    report = {
        "schema": 1,
        "scope": "offline bounded composition; pinned accumulated H2 base versus 29F278 + 1FF3C4 + 254CA8 candidate slots",
        "base_sha256": sha(base), "cursor_image_sha256": sha(cursor),
        "query_ips_sha256": sha(query_ips), "cumulative_sha256": sha(cumulative),
        "image_bytes": len(cumulative), "changed_byte_count": len(changed),
        "changed_ranges": [[hex(a), hex(b)] for a, b in actual],
        "slot_sizes": {"0x0029f278_candidate": 1028, "0x001ff3c4_candidate": 880,
                       "0x00254ca8_candidate": 640},
        "title_calc_scenarios": calc_rows,
        "mover_plus_logical_service_scenarios": query_rows,
        "limits": [
            "TitleConfig_Calc harness models unrelated outer services and the logical-query boundary; it executes the actual cursor code from each image.",
            "Mover scenarios execute the selected image's 0x001FF3C4 and 0x00254CA8 bodies, with lower logical-query, axis-reader and angle services controlled by deterministic seams.",
            "The 0x0027FBC8 no-write output domain remains unresolved and is excluded; these fixtures force both output floats to be written.",
            "Synthetic RAM fixtures do not establish physical controls, natural scheduling, runtime audio, emulator behavior or whole-game equivalence.",
        ],
    }
    (out / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = run(args.output)
    print(json.dumps({"cumulative_sha256": report["cumulative_sha256"],
                      "changed_ranges": report["changed_ranges"],
                      "title_calc": report["title_calc_scenarios"],
                      "mover_query": [{k: r[k] for k in ("label", "passed", "trace_count")}
                                      for r in report["mover_plus_logical_service_scenarios"]]}, indent=2))
    return 1 if any(not row["passed"] for row in
                    report["title_calc_scenarios"] + report["mover_plus_logical_service_scenarios"]) else 0


if __name__ == "__main__":
    raise SystemExit(main())
