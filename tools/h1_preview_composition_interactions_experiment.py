"""Private differential for maximal jointly reachable preview dependencies."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tools import h1_preview_full_composition_experiment as base

IMAGE = base.IMAGE
IMAGE_SHA = base.IMAGE_SHA


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def interaction_cases() -> list[dict]:
    # Three common-tail track entries are independent byte gates (+87/+88/+89).
    # The helper's own interpolation and endpoint/setter arms are mutually
    # exclusive at its unsigned-duration > signed-progress branch.
    helper_interp_rows = [(1, 2, 3, 4, 8, 1), (10, 20, 30, 40, 8, 1)]
    helper_endpoint_rows = [(1, 2, 3, 4, 4, 0),
                            (10, 20, 30, 40, 8, 1),
                            (11, 21, 31, 41, 8, 1)]
    sequence_for_setter = [(1, 0), (2, 1)]
    scale_rows = [(1.0, 5.0, 8, 1)]
    translation_rows = [(2.0, 6.0, 8, 1)]
    selector_ordinary = [(7, 0), (3, 0)]

    # Main helper interpolates (two divide calls), then all three tail bodies
    # execute: scale and translation endpoint stores, selector row transition.
    obj = base.fixture(gate=(0, 0), helper_table=base.HELPER_ROWS,
        progress=1, direction=0, scale_gate=0, translation_gate=0,
        selector_gate=0, scale_table=base.SCALE_ROWS, scale_progress=8,
        scale_direction=1, translation_table=base.TRANSLATION_ROWS,
        translation_progress=8, translation_direction=1,
        selector_table=base.SELECTOR_ROWS)
    first = base.case_data("helper interpolation + scale endpoint + translation endpoint + selector row advance",
        obj, helper_interp_rows, scale_rows=scale_rows,
        translation_rows=translation_rows, selector_rows=selector_ordinary)

    # Main helper takes endpoint->setter. Both floating track dependencies
    # interpolate, and selector takes its ordinary row-advance path.
    obj = base.fixture(gate=(0, 0), helper_table=base.HELPER_ROWS,
        progress=4, direction=0, enable=1, helper_sequence=base.HELPER_SEQUENCE,
        scale_gate=0, translation_gate=0, selector_gate=0,
        scale_table=base.SCALE_ROWS, scale_progress=1, scale_direction=0,
        translation_table=base.TRANSLATION_ROWS, translation_progress=1,
        translation_direction=0, selector_table=base.SELECTOR_ROWS)
    second = base.case_data("helper setter + scale interpolation + translation interpolation + selector row advance",
        obj, helper_endpoint_rows, sequence_for_setter,
        scale_rows=scale_rows, translation_rows=translation_rows,
        selector_rows=selector_ordinary)

    # Main helper interpolation leaves +84/+78 alone; the selector can consume
    # the same sequence pointer in its distinct layout while the scale and
    # translation tracks also interpolate.
    obj = base.fixture(gate=(0, 0), helper_table=base.HELPER_ROWS,
        progress=1, direction=1, enable=1, helper_sequence=base.SELECTOR_SEQUENCE,
        scale_gate=0, translation_gate=0, selector_gate=0,
        scale_table=base.SCALE_ROWS, scale_progress=1, scale_direction=1,
        translation_table=base.TRANSLATION_ROWS, translation_progress=1,
        translation_direction=0, selector_table=base.SELECTOR_ROWS,
        selector_progress=0)
    third = base.case_data("helper + scale + translation interpolation with selector sequence selection",
        obj, helper_interp_rows, scale_rows=scale_rows,
        translation_rows=translation_rows,
        selector_rows=[(7, 0), (-1, 0)], selector_seq_words=[0, 1],
        lookup_ids=[-1, 42])
    # The pinned selector reads the 28-byte sequence record word at +8
    # (0x2B1D34-0x2B1D40); the older shared fixture writer placed this word
    # at +0x14. Keep the shared runner untouched and encode the two records
    # at the original's actual offsets for this interaction fixture.
    corrected = bytearray(third["data"])
    sequence_offset = base.SELECTOR_SEQUENCE - base.DATA
    struct.pack_into("<i", corrected, sequence_offset + 8, 0)
    struct.pack_into("<i", corrected, sequence_offset + 8 + 28, 1)
    third["data"] = bytes(corrected)
    return [first, second, third]


def expected_call_names(case_name: str) -> list[str]:
    if case_name.startswith("helper setter"):
        return ["setter", "scale", "translation", "selector"]
    return ["divide", "divide", "scale", "translation", "selector"]


def run(output: Path) -> dict:
    output.mkdir(parents=True, exist_ok=False)
    image = IMAGE.read_bytes()
    if sha(image) != IMAGE_SHA:
        raise ValueError("pinned image identity mismatch")
    # Recheck all six original spans before executing either composition.
    component_identities = {}
    for name, (address, size, expected) in base.COMPONENTS.items():
        body = image[address - base.TEXT:address - base.TEXT + size]
        if len(body) != size or sha(body) != expected:
            raise ValueError(f"pinned {name} body identity mismatch")
        component_identities[name] = {"entry": hex(address), "size": size,
                                      "sha256": sha(body)}

    linked = base.build_candidate(output / "candidate-build")
    cases = interaction_cases()
    results = [base.compare(image, linked, case) for case in cases]

    # Targeted setter mutation on a case where scale, translation, and selector
    # also execute nontrivial bodies in the same helper invocation.
    setter = base.SOURCES["setter"].read_text(encoding="utf-8")
    anchor = "write_u16(object + 0x50, static_cast<uint16_t>(row_index));"
    if setter.count(anchor) != 1:
        raise ValueError("setter mutation anchor is not unique")
    mutant_dir = output / "negative-control"
    mutant_dir.mkdir(parents=True, exist_ok=False)
    mutant_source = mutant_dir / "setter_missing_animation_index_store.cpp"
    mutant_source.write_text(setter.replace(anchor,
        "/* mutation omits the +0x50 animation index store */"), encoding="utf-8")
    mutant_sources = dict(base.SOURCES)
    mutant_sources["setter"] = mutant_source
    mutant = base.build_candidate(mutant_dir / "candidate-build", mutant_sources)
    setter_case = next(c for c in cases if c["name"].startswith("helper setter"))
    mutation_result = base.compare(image, linked, setter_case, linked_mutant=mutant)
    negative_control = {"name": "missing_setter_0x50_animation_index_store",
        "detected": not mutation_result["passed"], "errors": mutation_result["errors"],
        "mutant_source_sha256": sha(mutant_source.read_bytes()),
        "mutant_elf_sha256": sha(mutant["elf"].read_bytes()), "case": mutation_result}

    expected = {c["name"]: expected_call_names(c["name"]) for c in cases}
    observed = {c["name"]: [call["name"] for call in c["original"]["calls"]]
                for c in results}
    result = {"schema_version": 1, "task_id": "h1-preview-composition-interactions",
        "passed": all(c["passed"] for c in results) and negative_control["detected"]
                  and observed == expected,
        "reference_image_sha256": sha(image), "original_components": component_identities,
        "candidate": linked["meta"], "cases": results, "case_count": len(results),
        "expected_call_names": expected, "observed_call_names": observed,
        "negative_control": negative_control,
        "gate_analysis": {
            "early_returns": "Null helper pointer and the both-negative signed +4/+8 gate return before all dependencies.",
            "common_tail": "On continuing paths, helper always calls scale, translation, selector in that order.",
            "independent_track_gates": "+0x87/+0x88/+0x89 and each corresponding table pointer can all be enabled/non-null together, so scale+translation+selector bodies can all execute in one call.",
            "helper_interpolation_vs_setter": "Mutually exclusive: duration > signed progress enters interpolation/divide; otherwise endpoint handling can reach setter only under row_mode==0, enabled/non-null sequence and ordinary/restart entry conditions.",
            "maximum_reachable_sets": [
                "divide + scale + translation + selector (helper interpolation arm)",
                "setter + scale + translation + selector (helper endpoint/sequence arm)"],
            "not_claimed": "A single helper call cannot execute both its divide interpolation and setter sequence update; fixtures do not manufacture that impossible path."
        },
        "projection": ["fault/termination sentinel", "r0", "r4-r11 and SP", "d8-d15", "FPSCR",
                       "full 0x20000-byte mapped data snapshot/digest", "caller-owned stack",
                       "ordered direct-callee names and arguments"],
        "evidence": {"compiled": "passed", "arm_differential": "partial_synthetic_joint_paths",
                     "caller": "partial_static_call_graph", "runtime": "not_run"},
        "limitations": [
            "Three valid synthetic, non-aliasing fixtures exercise the maximal jointly reachable dependency sets; they do not model constructed H1 objects or asset/runtime lifecycle.",
            "The helper divide path uses positive nonzero u16 duration only; divide-by-zero and arbitrary signed denominator behavior are outside this domain.",
            "The comparison inherits the full-composition projection: caller-saved scratch GPRs/flags, memory access multiplicity/order, below-SP spill residue, invalid pointers/indices, aliasing, concurrency, MMIO and live caller/runtime behavior are unvalidated.",
            "The helper's divide and setter arms are mutually exclusive in one invocation; both combinations are covered across separate fixtures, not conflated."
        ]}
    report = output / "report.json"
    report.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True,
                        help="new private output directory")
    args = parser.parse_args()
    output = args.output if args.output.is_absolute() else ROOT / args.output
    report = run(output)
    passed = sum(c["passed"] for c in report["cases"])
    print(f"preview joint paths: {'PASS' if report['passed'] else 'FAIL'} "
          f"{passed}/{report['case_count']}; setter mutation="
          f"{'detected' if report['negative_control']['detected'] else 'missed'}; "
          f"report={output / 'report.json'}")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
