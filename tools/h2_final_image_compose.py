#!/usr/bin/env python3
"""Compose reviewed H2 callback, mapper, and FillPair replacements."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import random
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.h2_calc_code_patch import apply_ips, encode_ips

CALLBACK_VALIDATOR = ROOT / "tools/h2_combined_offline_validation.py"
CALLER_VALIDATOR = ROOT / "tools/h2_offline_caller_composition.py"
MAPPER_NEGATIVE_OBJECT = ROOT / "build/agent-work/H2-semantic/h2-config-mapper-production-integration/run-003/checks/production-mapper-patch/negative-control-candidates.o"
SECONDARY_NEGATIVE_OBJECT = ROOT / "build/agent-work/H2-semantic/h2-config-mapper-production-integration/run-004/checks/final-image-validation/secondary-negative-control-build/h2_secondary_candidate.o"
INITIALIZER_NEGATIVE_OBJECT = ROOT / "build/agent-work/H2-semantic/h2-config-mapper-production-integration/run-004/checks/final-image-validation/initializer-negative-control-build/h2_init_orchestration_candidate.o"
FILL_NEGATIVE_OBJECT = ROOT / "build/agent-work/H2-semantic/h2-pair-fill-production-integration/run-003/checks/helper-differential/wrong_fill_pair.o"

ORIGINAL = ROOT / "extracted/exefs/code.bin"
CALLBACK_DIR = ROOT / "build/agent-work/H2-semantic/h2-thumb-reintegrate-final-image/run-004/combined-build-final"
MAPPER_DIR = ROOT / "build/agent-work/H2-semantic/h2-config-mapper-production-integration/run-008/checks/production-mapper-patch"
FILL_DIR = ROOT / "build/agent-work/H2-semantic/h2-pair-fill-production-integration/run-003/checks/production-fill-patch"
RUN013 = ROOT / "build/agent-work/H2-semantic/h2-init-ready-final-image/run-013/combined-build-final/code.combined.bin"
ORIGINAL_SHA256 = "1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558"
CALLBACK_SHA256 = "cd095feb4c8034874a2ef4661356cb131e0e240cfc907f454f12b83d05c13bf4"
MAPPER_SHA256 = "97b6c2ab9ea7f15904bbee3ad42115599bd3529220dbfba818a77bbbcfbe321c"
FILL_SHA256 = "5e9aa08b449985f012e24400c45b4b037e4a0d5d069723b6cfa7ccf83300d8fa"
RUN013_SHA256 = "7b2bc2983a890e1c4cf1ae71beca9f574260d98d6cfcdffb3bbb34bd3eb2b291"
MAPPER_IPS_SHA256 = "72b9c68d2aca701c899978adeb793698032097a2599d70ab9c90a0361336e214"
FILL_IPS_SHA256 = "5b0a75a1526aec8db88b0f02cf0f9eef98e657a51a5b2bb5e1993932b9d5a4c2"
FILL_VMA = 0x0027EDF8
TEXT_VMA = 0x00100000


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def verify_file(path: Path, expected: str, label: str) -> bytes:
    data = path.read_bytes()
    actual = sha256(data)
    if actual != expected:
        raise ValueError(f"{label} SHA-256 mismatch: expected {expected}, got {actual} ({path})")
    return data


def verify_ips(base: bytes, patch_path: Path, expected_patch_hash: str,
               expected_result_hash: str, label: str) -> bytes:
    patch = verify_file(patch_path, expected_patch_hash, f"{label} IPS")
    result = apply_ips(base, patch)
    if sha256(result) != expected_result_hash:
        raise ValueError(f"{label} IPS round-trip result hash mismatch")
    return result


def verify_identity(path_text: str, expected: str, label: str) -> dict:
    path = Path(path_text)
    if not path.is_absolute():
        path = ROOT / path
    actual = sha256(path.read_bytes())
    return {"path": str(path), "expected_sha256": expected, "observed_sha256": actual,
            "matches": actual == expected}


def locate_hash(root: Path, expected: str) -> list[Path]:
    matches = []
    for path in root.rglob("*.o"):
        try:
            if sha256(path.read_bytes()) == expected:
                matches.append(path)
        except OSError:
            pass
    return matches


def contiguous_records(original: bytes, final: bytes) -> list[tuple[int, bytes]]:
    records: list[tuple[int, bytes]] = []
    cursor = 0
    while cursor < len(original):
        if original[cursor] == final[cursor]:
            cursor += 1
            continue
        start = cursor
        cursor += 1
        while cursor < len(original) and original[cursor] != final[cursor]:
            cursor += 1
        records.append((start, final[start:cursor]))
    return records


def compose_images(original: bytes, callback: bytes, mapper: bytes, fill: bytes,
                   callback_manifest: dict, mapper_manifest: dict,
                   fill_manifest: dict) -> tuple[bytes, bytes, dict]:
    if not (len(original) == len(callback) == len(mapper) == len(fill)):
        raise ValueError("all input code images must have identical lengths")
    if sha256(original) != ORIGINAL_SHA256:
        raise ValueError("pinned original code.bin identity mismatch")
    if sha256(callback) != CALLBACK_SHA256:
        raise ValueError("reviewed callback image identity mismatch")
    if sha256(mapper) != MAPPER_SHA256 or mapper_manifest.get("patched_sha256") != MAPPER_SHA256:
        raise ValueError("reviewed mapper image identity mismatch")
    if sha256(fill) != FILL_SHA256 or fill_manifest.get("patched_sha256") != FILL_SHA256:
        raise ValueError("reviewed FillPair image identity mismatch")
    if callback_manifest.get("original_sha256") != ORIGINAL_SHA256:
        raise ValueError("callback manifest is not based on pinned original")

    final = bytearray(callback)
    allowed: set[int] = set()
    callback_ranges = []
    for row in callback_manifest.get("ips_records", []):
        offset, length = int(row["offset"], 0), int(row["length"])
        allowed.update(range(offset, offset + length))
        callback_ranges.append({"offset": hex(offset), "length": length,
                                "payload_sha256": row["sha256"]})

    map_records = mapper_manifest["mapper_replacements"]["incoming_reference_audit"]["patch_records"]
    mapper_ranges = []
    for row in map_records:
        offset, length = int(row["offset"], 0), int(row["span"])
        if bytes(mapper[offset:offset + length]) == bytes(original[offset:offset + length]):
            raise ValueError(f"mapper replacement unexpectedly equals original at {row['address']}")
        final[offset:offset + length] = mapper[offset:offset + length]
        allowed.update(range(offset, offset + length))
        mapper_ranges.append({"address": row["address"], "offset": hex(offset),
                              "length": length, "replacement_sha256": sha256(mapper[offset:offset + length])})

    fill_data = fill_manifest["fill_pair_replacement"]
    fill_offset = int(fill_data["address"], 0) - TEXT_VMA
    fill_size = int(fill_data["size"])
    body = bytes.fromhex(fill_data["body_hex"])
    if len(body) != fill_size or bytes(fill[fill_offset:fill_offset + fill_size]) != body:
        raise ValueError("FillPair body does not match the reviewed manifest")
    if bytes(original[fill_offset:fill_offset + fill_size]) == body:
        raise ValueError("FillPair body unexpectedly equals original")
    final[fill_offset:fill_offset + fill_size] = body
    allowed.update(range(fill_offset, fill_offset + fill_size))

    final_bytes = bytes(final)
    changed = {i for i, (a, b) in enumerate(zip(original, final_bytes)) if a != b}
    if not changed <= allowed:
        first = min(changed - allowed)
        raise ValueError(f"unauthorized changed byte at file offset {first:#x}")
    # The already matching CopyPair entry/body are left untouched by this composition.
    copy_pair = (0x002ADB40 - TEXT_VMA, 20)
    if original[copy_pair[0]:sum(copy_pair)] != final_bytes[copy_pair[0]:sum(copy_pair)]:
        raise ValueError("composition unexpectedly changed CopyPair")

    records = contiguous_records(original, final_bytes)
    ips = encode_ips(records, len(original))
    if apply_ips(original, ips) != final_bytes:
        raise ValueError("final IPS round-trip mismatch")
    record_manifest = [{"offset": hex(offset), "length": len(payload), "sha256": sha256(payload)}
                       for offset, payload in records]
    manifest = {
        "schema": 1,
        "kind": "composed H2 production image (offline evidence; runtime not asserted)",
        "original_sha256": sha256(original),
        "patched_sha256": sha256(final_bytes),
        "ips_sha256": sha256(ips),
        "ips_records": record_manifest,
        "changed_byte_count": len(changed),
        "placements": callback_manifest["placements"],
        "composition": {
            "callback_image_sha256": sha256(callback),
            "callback_manifest_sha256": sha256(json.dumps(callback_manifest, sort_keys=True).encode()),
            "callback_authorized_ranges": callback_ranges,
            "mapper_image_sha256": sha256(mapper),
            "mapper_ips_sha256": mapper_manifest["ips_sha256"],
            "mapper_ranges": mapper_ranges,
            "fill_image_sha256": sha256(fill),
            "fill_ips_sha256": fill_data["ips_sha256"],
            "fill_pair": {"address": fill_data["address"], "size": fill_size,
                          "body_hex": body.hex(), "source_sha256": fill_data["source_sha256"],
                          "object_sha256": fill_data["object_sha256"]},
            "copy_pair": {"address": hex(TEXT_VMA + copy_pair[0]), "size": copy_pair[1],
                          "preserved": True},
            "patch_chain": [
                {"kind": "reviewed Thumb-corrected five-callback image", "result_sha256": sha256(callback)},
                {"kind": "three mapper production slot overlays", "source_image_sha256": sha256(mapper)},
                {"kind": "FillPair production slot overlay", "source_image_sha256": sha256(fill)},
            ],
        },
    }
    return final_bytes, ips, manifest


def build(output: Path) -> dict:
    if output.exists():
        raise FileExistsError(f"output directory already exists: {output}")
    output.mkdir(parents=True)
    original = verify_file(ORIGINAL, ORIGINAL_SHA256, "original")
    cb_manifest_path = CALLBACK_DIR / "manifest.json"
    map_manifest_path = MAPPER_DIR / "manifest.json"
    fill_manifest_path = FILL_DIR / "manifest.json"
    cbm, mapm, fillm = (read_json(x) for x in (cb_manifest_path, map_manifest_path, fill_manifest_path))
    callback = verify_file(CALLBACK_DIR / "code.combined.bin", CALLBACK_SHA256, "callback image")
    mapper = verify_file(MAPPER_DIR / "code.h2-mappers.bin", MAPPER_SHA256, "mapper image")
    fill = verify_file(FILL_DIR / "code.h2-fill-pair.bin", FILL_SHA256, "FillPair image")
    run013 = verify_file(RUN013, RUN013_SHA256, "run-013 mapper base")
    verify_ips(run013, MAPPER_DIR / "code.h2-mappers.ips", MAPPER_IPS_SHA256, MAPPER_SHA256, "mapper")
    mapper_image = verify_file(MAPPER_DIR / "code.h2-mappers.bin", MAPPER_SHA256, "mapper image")
    verify_ips(mapper_image, FILL_DIR / "code.h2-fill-pair.ips", FILL_IPS_SHA256, FILL_SHA256, "FillPair")
    callback_ips = verify_file(CALLBACK_DIR / "code.combined.ips", cbm["ips_sha256"], "callback IPS")
    if apply_ips(original, callback_ips) != callback:
        raise ValueError("callback IPS round-trip mismatch")
    if sha256(callback_ips) != "08dc412ae2045858cc5e087ca97527edd32622311c2bd0b9a219276fec7ba758":
        raise ValueError("callback IPS identity mismatch")

    identities = []
    for group, meta in cbm.get("sources", {}).items():
        identities.append({"kind": "callback_source", "name": group,
                           **verify_identity(meta["path"], meta["sha256"], f"callback source {group}")})
        object_matches = locate_hash(ROOT / "build/agent-work/H2-semantic", meta["object_sha256"])
        identities.append({"kind": "callback_object", "name": group,
                           "expected_sha256": meta["object_sha256"], "matches": bool(object_matches),
                           "paths": [str(path) for path in object_matches]})
    for address, meta in mapm["mapper_replacements"]["functions"].items():
        identities.append({"kind": "mapper_source", "name": address,
                           **verify_identity(meta["source"], meta["source_sha256"], f"mapper source {address}")})
    fill_data = fillm["fill_pair_replacement"]
    identities.append({"kind": "fill_source", "name": fill_data["symbol"],
                       **verify_identity(fill_data["source"], fill_data["source_sha256"], "FillPair source")})
    # Object hashes are recorded in the reviewed manifests; locate the exact files from their paths.
    for address, meta in mapm["mapper_replacements"]["functions"].items():
        identities.append({"kind": "mapper_object", "name": address,
                           **verify_identity(meta["object"], meta["object_sha256"], f"mapper object {address}")})
    identities.append({"kind": "fill_object", "name": fill_data["symbol"],
                       **verify_identity(fill_data["object"], fill_data["object_sha256"], "FillPair object")})
    mismatches = [row for row in identities if not row["matches"]]
    final, ips, manifest = compose_images(original, callback, mapper, fill, cbm, mapm, fillm)
    manifest["source_and_object_identities"] = identities
    manifest["source_identity_mismatches"] = mismatches
    manifest["input_artifacts"] = {
        "callback_image": {"path": str(CALLBACK_DIR / "code.combined.bin",), "sha256": sha256(callback)},
        "callback_ips": {"path": str(CALLBACK_DIR / "code.combined.ips"), "sha256": sha256(callback_ips)},
        "callback_manifest": {"path": str(cb_manifest_path), "sha256": sha256(cb_manifest_path.read_bytes())},
        "mapper_image": {"path": str(MAPPER_DIR / "code.h2-mappers.bin"), "sha256": sha256(mapper)},
        "mapper_ips": {"path": str(MAPPER_DIR / "code.h2-mappers.ips"), "sha256": MAPPER_IPS_SHA256},
        "mapper_manifest": {"path": str(map_manifest_path), "sha256": sha256(map_manifest_path.read_bytes())},
        "fill_image": {"path": str(FILL_DIR / "code.h2-fill-pair.bin"), "sha256": sha256(fill)},
        "fill_ips": {"path": str(FILL_DIR / "code.h2-fill-pair.ips"), "sha256": FILL_IPS_SHA256},
        "fill_manifest": {"path": str(fill_manifest_path), "sha256": sha256(fill_manifest_path.read_bytes())},
        "run013_base": {"path": str(RUN013), "sha256": sha256(run013)},
    }
    (output / "code.h2-final.bin").write_bytes(final)
    (output / "code.h2-final.ips").write_bytes(ips)
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return {"image_sha256": sha256(final), "ips_sha256": sha256(ips),
            "manifest_sha256": sha256((output / "manifest.json").read_bytes()),
            "changed_byte_count": manifest["changed_byte_count"], "image": str(output / "code.h2-final.bin"),
            "ips": str(output / "code.h2-final.ips"), "manifest": str(output / "manifest.json")}


def validate_offline(image_path: Path, manifest_path: Path, output: Path) -> dict:
    """Run the H2 differential families against one exact composed image, without compiling."""
    from tools.asm_diff import extract_elf_functions_detailed
    from tools.h2_combined_offline_validation import (
        validate_calc_sequences, validate_draw, validate_ready_gate,
        _normalize_initializer_string_pointers,
    )
    from tools.h2_secondary_experiment import ENTRY as SECONDARY_ENTRY, Run as SecondaryRun, compare as compare_secondary, make_cases as secondary_cases
    from tools.h2_init_orchestration_experiment import INIT as INIT_ENTRY, InitRun, build_cases as initializer_cases, compare as compare_initializer
    from tools.h2_config_mapper_experiment import MAPPERS, MapperRunner, expected_index, make_case
    from tools.h2_pair_fill_production_experiment import ADDRESS as FILL_ADDRESS, HIGH_PATTERNS, DATA, DATA_SIZE, STACK_SIZE
    from tools.semantic_experiment import Case, Runner, difference

    if output.exists():
        raise FileExistsError(output)
    output.mkdir(parents=True)
    original, patched = ORIGINAL.read_bytes(), image_path.read_bytes()
    manifest = read_json(manifest_path)
    if sha256(original) != ORIGINAL_SHA256 or manifest.get("patched_sha256") != sha256(patched):
        raise ValueError("offline validation input identities do not match the supplied final manifest")
    start = time.perf_counter()
    callbacks = {
        "draw": validate_draw(original, patched),
        "calc": validate_calc_sequences(original, patched, [7, 20261024]),
        "ready_gate": validate_ready_gate(original, patched),
    }

    # Reuse already-built, previously reviewed negative-control objects so this
    # zero-compiler task never starts a compiler process.
    sec_obj = extract_elf_functions_detailed(SECONDARY_NEGATIVE_OBJECT)
    init_obj = extract_elf_functions_detailed(INITIALIZER_NEGATIVE_OBJECT)
    mapper_obj = extract_elf_functions_detailed(MAPPER_NEGATIVE_OBJECT)
    fill_obj = extract_elf_functions_detailed(FILL_NEGATIVE_OBJECT)
    seeds = [7, 20261024]
    secondary_rows, secondary_first = [], None
    for seed in seeds:
        for case in secondary_cases():
            left = SecondaryRun(original, SECONDARY_ENTRY, None, case, seed).run()
            right = SecondaryRun(patched, SECONDARY_ENTRY, None, case, seed).run()
            diff = compare_secondary(left, right)
            secondary_rows.append({"seed": seed, "case": case["label"], "passed": diff is None, "difference": diff})
            if diff and secondary_first is None: secondary_first = {"seed": seed, "case": case["label"], "difference": diff}
    sec_name = "candidate_002caef0_wrong_count"
    sec_body = sec_obj[sec_name][0]
    sec_mutant = bytearray(patched)
    sec_cave = 0x003FEED4 - TEXT_VMA
    sec_mutant[sec_cave:sec_cave + len(sec_body)] = sec_body
    sec_case = next(c for c in secondary_cases() if c["label"] == "both-loops-distinct")
    sec_neg_diff = compare_secondary(
        SecondaryRun(original, SECONDARY_ENTRY, None, sec_case, seeds[0]).run(),
        SecondaryRun(bytes(sec_mutant), SECONDARY_ENTRY, None, sec_case, seeds[0]).run())
    callbacks["secondary"] = {"cases": secondary_rows, "case_count": len(secondary_rows),
                              "cases_passed": sum(x["passed"] for x in secondary_rows),
                              "first_counterexample": secondary_first,
                              "negative_control": {"detected": sec_neg_diff is not None, "difference": sec_neg_diff}}

    init_rows, init_first = [], None
    for seed in seeds:
        for case in initializer_cases(seed, samples=2):
            left = InitRun(original, None, INIT_ENTRY, seed=seed).run(case)
            right = InitRun(patched, None, INIT_ENTRY, seed=seed).run(case)
            leftn, rightn = dict(left), dict(right)
            leftn["trace"] = _normalize_initializer_string_pointers(left["trace"])
            rightn["trace"] = _normalize_initializer_string_pointers(right["trace"])
            diff = compare_initializer(leftn, rightn)
            init_rows.append({"seed": seed, "case": case["label"], "passed": diff is None, "difference": diff})
            if diff and init_first is None: init_first = {"seed": seed, "case": case["label"], "difference": diff}
    init_name = "candidate_002f4ca0_wrong_count"
    init_body = bytearray(init_obj[init_name][0])
    old = (0x002F4E84).to_bytes(4, "little")
    new = (0x0042AB78).to_bytes(4, "little")
    if init_body.count(old) != 1: raise ValueError("prebuilt initializer negative-control pointer drift")
    init_body = init_body.replace(old, new)
    init_mutant = bytearray(patched)
    init_off = 0x002F4CA0 - TEXT_VMA
    init_mutant[init_off:init_off + 572] = bytes(572)
    init_mutant[init_off:init_off + len(init_body)] = init_body
    init_case = initializer_cases(seeds[0], samples=2)[0]
    nleft = InitRun(original, None, INIT_ENTRY, seed=seeds[0]).run(init_case)
    nright = InitRun(bytes(init_mutant), None, INIT_ENTRY, seed=seeds[0]).run(init_case)
    nleft["trace"] = _normalize_initializer_string_pointers(nleft["trace"])
    nright["trace"] = _normalize_initializer_string_pointers(nright["trace"])
    init_neg_diff = compare_initializer(nleft, nright)
    callbacks["initializer"] = {"cases": init_rows, "case_count": len(init_rows),
                                 "cases_passed": sum(x["passed"] for x in init_rows),
                                 "first_counterexample": init_first,
                                 "negative_control": {"detected": init_neg_diff is not None, "difference": init_neg_diff}}

    mapper_reports = []
    for address, (candidate_name, boundaries) in MAPPERS.items():
        table = {0x0021F39C: 0x004077F6, 0x002CAB70: 0x004077EB, 0x002E0AF4: 0x00407801}[address]
        a, b = MapperRunner(original, address, table), MapperRunner(patched, address, table)
        rng = random.Random(7 ^ address)
        rows = []
        values = [(f"byte-{v}", v) for v in range(256)] + [(f"seeded-{i}", rng.randrange(256)) for i in range(256)]
        for label, value in values:
            case = make_case(value, random.Random((7 ^ address) + value), label)
            left, right = a.run(case), b.run(case)
            fail = ("fault" if left.fault or right.fault else "not stopped" if not left.stopped or not right.stopped else
                    "return mismatch" if left.result != right.result else
                    "memory or ABI difference" if difference(left, right) else
                    "expected result mismatch" if right.result != expected_index(value, boundaries) else None)
            rows.append({"case": label, "passed": fail is None, "difference": fail})
        wrong = mapper_obj["candidate_002cab70_wrong_map"][0] if address == 0x002CAB70 else None
        neg_detected = None
        if wrong is not None:
            nc = make_case(11, random.Random(11), "mapper-negative-control")
            neg_detected = difference(a.run(nc), MapperRunner(patched, address, table, wrong).run(nc)) is not None
        mapper_reports.append({"address": hex(address), "case_count": len(rows),
                               "cases_passed": sum(x["passed"] for x in rows), "negative_control_detected": neg_detected,
                               "first_counterexample": next((x for x in rows if not x["passed"]), None)})

    fill_original, fill_final = Runner(original, FILL_ADDRESS), Runner(patched, FILL_ADDRESS)
    wrong_fill = fill_obj["wrong_fill_pair"][0]
    fill_rng = random.Random(7 ^ FILL_ADDRESS)
    fill_count, fill_first = 0, None
    for off in range(4):
        for high in HIGH_PATTERNS:
            for low in range(256):
                regs = [fill_rng.getrandbits(32) for _ in range(13)]
                regs[0], regs[1] = DATA + 0x400 + off, high | low
                case = Case(f"dst-{off}-high-{high:08x}-low-{low:02x}", tuple(regs),
                            fill_rng.randbytes(DATA_SIZE), fill_rng.randbytes(STACK_SIZE), fill_rng.getrandbits(4) << 28)
                err = difference(fill_original.run(case), fill_final.run(case), returns_value=True)
                if err:
                    fill_first = {"case": case.label, "difference": err}; break
                fill_count += 1
            if fill_first: break
        if fill_first: break
    nc = Case("wrong-mask", tuple([DATA + 0x500, 0xABCD1255] + [0] * 11),
              bytes(DATA_SIZE), bytes(STACK_SIZE), 0)
    fill_negative_diff = difference(fill_original.run(nc), Runner(patched, FILL_ADDRESS, wrong_fill).run(nc), returns_value=True)
    fill_report = {"cases_expected": 4096, "cases_passed": fill_count, "first_counterexample": fill_first,
                   "negative_control_detected": fill_negative_diff == "data memory differs",
                   "negative_control_difference": fill_negative_diff}

    (output / "callbacks.json").write_text(json.dumps(callbacks, indent=2) + "\n", encoding="utf-8")
    (output / "mappers.json").write_text(json.dumps(mapper_reports, indent=2) + "\n", encoding="utf-8")
    (output / "fill_pair.json").write_text(json.dumps(fill_report, indent=2) + "\n", encoding="utf-8")
    # Caller harness consumes the same final image and manifest, writes its own report.
    caller_dir = output / "caller"
    proc = subprocess.run([sys.executable, str(CALLER_VALIDATOR), "--code", str(ORIGINAL),
                           "--patched-image", str(image_path), "--manifest", str(manifest_path),
                           "--final-initializer", "--output", str(caller_dir)],
                          cwd=ROOT, capture_output=True, text=True)
    (output / "caller.stdout.txt").write_text(proc.stdout, encoding="utf-8")
    (output / "caller.stderr.txt").write_text(proc.stderr, encoding="utf-8")
    caller_report_path = caller_dir / "report.json"
    caller_report = read_json(caller_report_path) if caller_report_path.exists() else {}
    caller_build = caller_report.get("build", {})
    report = {"schema": 1, "image_sha256": sha256(patched), "manifest_sha256": sha256(manifest_path.read_bytes()),
              "callbacks": {k: {"passed": v.get("cases_passed", v.get("sequences_passed", 0)),
                                "total": v.get("case_count", v.get("sequence_count", 0))} for k, v in callbacks.items()},
              "mapper_results": mapper_reports, "fill_pair": fill_report,
              "caller_exit_code": proc.returncode, "caller_report": str(caller_dir / "report.json"),
              "prebuilt_control_objects": {str(p): sha256(p.read_bytes()) for p in
                  (MAPPER_NEGATIVE_OBJECT, SECONDARY_NEGATIVE_OBJECT, INITIALIZER_NEGATIVE_OBJECT, FILL_NEGATIVE_OBJECT)},
              "compiler_processes_started": int(caller_build.get("compile_exit") is not None),
              "caller_compile_exit": caller_build.get("compile_exit"),
              "caller_compile_command": caller_build.get("compile_command"),
              "source_identity_mismatches": manifest.get("source_identity_mismatches", []),
              "runtime": "not_run",
              "elapsed_seconds": round(time.perf_counter() - start, 3)}
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="new task-local output directory")
    parser.add_argument("--validate-image", type=Path, help="run offline suites against a composed final image")
    parser.add_argument("--manifest", type=Path, help="manifest for --validate-image")
    args = parser.parse_args()
    result = (validate_offline(args.validate_image, args.manifest, args.output)
              if args.validate_image else build(args.output))
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
