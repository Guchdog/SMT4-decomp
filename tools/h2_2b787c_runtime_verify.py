#!/usr/bin/env python3
"""Run the bounded autonomous H2 scenario with a probe on 0x002B787C."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import struct

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools import h2_86928_runtime_verify as probe
from tools.h2_calc_code_patch import apply_ips, encode_ips

ADDRESS = 0x002B787C
IMAGE_BASE = 0x00100000
SPAN = 176
FINAL_BASE_IMAGE = ROOT / "build/agent-work/H2-semantic/h2-final-image-composition/run-001/composed-003/code.h2-final.bin"
FINAL_BASE_IPS = ROOT / "build/agent-work/H2-semantic/h2-final-image-composition/run-001/composed-003/code.h2-final.ips"
PRODUCTION_IMAGE = ROOT / "build/h2-2b787c-integration/staged-image/code.h2-2b787c.bin"
COMPOSED = ROOT / "build/h2-2b787c-integration/cumulative-runtime"
DIRECT_OBSERVATIONS: list[dict] = []
DIRECT_SEEN_RSP: set[int] = set()


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def changed_records(before: bytes, after: bytes) -> list[tuple[int, bytes]]:
    if len(before) != len(after):
        raise ValueError("cannot encode IPS for images with different lengths")
    rows: list[tuple[int, bytes]] = []
    i = 0
    while i < len(before):
        if before[i] == after[i]:
            i += 1
            continue
        start = i
        while i < len(before) and before[i] != after[i] and i - start < 0xFFFF:
            i += 1
        rows.append((start, after[start:i]))
    return rows


def compose() -> tuple[Path, Path, dict]:
    original_path = ROOT / "extracted/exefs/code.bin"
    original = original_path.read_bytes()
    base_image = FINAL_BASE_IMAGE.read_bytes()
    base_ips = FINAL_BASE_IPS.read_bytes()
    if apply_ips(original, base_ips) != base_image:
        raise SystemExit("pinned H2 cumulative IPS does not reproduce its image")
    offset = ADDRESS - IMAGE_BASE
    if base_image[offset:offset + SPAN] != original[offset:offset + SPAN]:
        raise SystemExit("cumulative H2 image already changes the target function slot")
    production = PRODUCTION_IMAGE.read_bytes()
    patched = bytearray(base_image)
    patched[offset:offset + SPAN] = production[offset:offset + SPAN]
    patched_bytes = bytes(patched)
    records = changed_records(original, patched_bytes)
    ips = encode_ips(records, len(original))
    if apply_ips(original, ips) != patched_bytes:
        raise SystemExit("cumulative runtime IPS round trip failed")
    COMPOSED.mkdir(parents=True, exist_ok=True)
    image_path = COMPOSED / "code.h2-2b787c-runtime.bin"
    ips_path = COMPOSED / "code.h2-2b787c-runtime.ips"
    manifest_path = COMPOSED / "manifest.json"
    image_path.write_bytes(patched_bytes)
    ips_path.write_bytes(ips)
    manifest = {
        "kind": "cumulative H2 image with 0x002B787C production replacement",
        "original_image_sha256": sha(original),
        "prior_cumulative_image_sha256": sha(base_image),
        "prior_cumulative_ips_sha256": sha(base_ips),
        "target": hex(ADDRESS),
        "target_slot_bytes": SPAN,
        "target_body_sha256": sha(patched_bytes[offset:offset + SPAN]),
        "new_cumulative_image_sha256": sha(patched_bytes),
        "new_cumulative_ips_sha256": sha(ips),
        "new_ips_record_count": len(records),
        "only_target_slot_added_to_prior_cumulative_image": all(
            base_image[i] == patched_bytes[i]
            for i in range(len(base_image)) if not offset <= i < offset + SPAN
        ),
        "ips_roundtrip": True,
        "runtime_scenario": "existing bounded H2 titleConfig scenario",
        "artifact_paths": {
            "image": image_path.relative_to(ROOT).as_posix(),
            "ips": ips_path.relative_to(ROOT).as_posix(),
        },
        "runtime": "not_run",
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return image_path, ips_path, manifest


def _read_reg(rsp, index: int) -> int:
    return probe.base.decode_r0(rsp.request(f"p{index:02x}".encode("ascii")))


def run_guest_helper_fixture(rsp) -> dict:
    """Execute the real guest function with a temporary stack-resident table."""
    base = probe.base
    return_pc = base.ADDR_TITLE_CONFIG_CALC
    original_regs = [_read_reg(rsp, index) for index in range(16)]
    original_sp = original_regs[13]
    handle = (original_sp + 0x400) & 0xFFFFFFFF
    records = (original_sp + 0x500) & 0xFFFFFFFF
    old_handle = base.rsp_read_mem(rsp, handle, 0x20)
    old_records = base.rsp_read_mem(rsp, records, 0x40)
    handle_data = bytearray(0x20)
    struct.pack_into("<I", handle_data, 0, records)
    struct.pack_into("<I", handle_data, 0x0C, 0)
    struct.pack_into("<I", handle_data, 0x14, 1)
    records_data = bytearray(0x40)
    struct.pack_into("<H", records_data, 0, 0xF801)
    struct.pack_into("<H", records_data, 0x20, 0xF802)
    observation = {"address": hex(ADDRESS), "entry_r0_handle": hex(handle),
                   "record_table": hex(records), "fixture_codes": ["0xF801", "0xF802"]}
    base.rsp_set_bp(rsp, return_pc)
    try:
        base.rsp_write_mem(rsp, handle, bytes(handle_data))
        base.rsp_write_mem(rsp, records, bytes(records_data))
        base.rsp_write_reg(rsp, 0, handle)
        base.rsp_write_reg(rsp, 14, return_pc)
        base.rsp_write_reg(rsp, 15, ADDRESS)
        stop = rsp.continue_to_stop()
        stopped_pc = _read_reg(rsp, 15)
        returned = _read_reg(rsp, 0)
        if stopped_pc != return_pc:
            raise RuntimeError(f"guest helper returned to {stopped_pc:#x}, expected {return_pc:#x}; {stop!r}")
        if returned != 1:
            raise RuntimeError(f"guest helper fixture expected count 1, got {returned:#x}")
        # Consume the actual guest return in the probe harness, as a one-word caller would.
        base.rsp_write_u32(rsp, handle + 0x1C, returned)
        consumed = base.rsp_read_u32(rsp, handle + 0x1C)
        observation.update({"return_pc": hex(stopped_pc), "raw_return_r0": returned,
                            "caller_probe_consumed_count": consumed,
                            "caller_probe_consumption_matched": consumed == returned,
                            "callee_saved_sp_matched": _read_reg(rsp, 13) == original_sp,
                            "stop_reply": stop.decode("ascii", errors="replace")})
        if not observation["caller_probe_consumption_matched"] or not observation["callee_saved_sp_matched"]:
            raise RuntimeError("guest helper runtime return/stack check failed")
        return observation
    finally:
        base.rsp_clear_bp(rsp, return_pc)
        base.rsp_write_mem(rsp, handle, old_handle)
        base.rsp_write_mem(rsp, records, old_records)
        for index, value in enumerate(original_regs):
            base.rsp_write_reg(rsp, index, value)


ORIGINAL_CALL_SET = probe.ORIGINAL_CALL_SET


def call_set_then_probe_once(rsp, cursor: int, row: int) -> dict:
    result = ORIGINAL_CALL_SET(rsp, cursor, row)
    if id(rsp) not in DIRECT_SEEN_RSP:
        DIRECT_SEEN_RSP.add(id(rsp))
        observation = run_guest_helper_fixture(rsp)
        DIRECT_OBSERVATIONS.append(observation)
        result["direct_line_count_runtime_probe"] = observation
    return result


probe.ORIGINAL_CALL_SET = call_set_then_probe_once
probe.event_signature = lambda event: (
    event["entry"]["r0"], event["return"]["r0"] if event["return"] else None
)
ORIGINAL_INSTRUMENTED_EXECUTE = probe.instrumented_execute


def instrumented_execute_with_fixture(*args, **kwargs) -> dict:
    first_observation = len(DIRECT_OBSERVATIONS)
    result = ORIGINAL_INSTRUMENTED_EXECUTE(*args, **kwargs)
    result["direct_line_count_runtime_probe"] = DIRECT_OBSERVATIONS[first_observation:]
    return result


probe.base.execute_h2_scenario = instrumented_execute_with_fixture


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    output_arg = next((Path(args[i + 1]) for i, value in enumerate(args[:-1])
                       if value == "--output-dir"), None)
    if output_arg is None:
        raise SystemExit("--output-dir is required")
    image_path, ips_path, manifest = compose()
    probe.HELPER = ADDRESS
    runtime_args = args + ["--final-image", str(image_path), "--final-ips", str(ips_path)]
    status = probe.main(runtime_args)
    report_path = output_arg.resolve() / "autonomous-gdb-verification.json"
    if report_path.exists():
        report = json.loads(report_path.read_text(encoding="utf-8"))
        report["line_count_runtime_probe"] = report.pop("helper_runtime_probe", {})
        report["line_count_runtime_probe"]["function"] = "AsdText_GetLineCount"
        report["line_count_runtime_probe"]["address"] = hex(ADDRESS)
        report["line_count_runtime_probe"]["invocation_mode"] = (
            "At the paused TitleConfig_Calc checkpoint, GDB supplies a temporary stack-resident "
            "one-argument fixture and sets guest PC to the real function entry; it captures r0, "
            "consumes that value in a probe-owned word, then restores registers and fixture memory."
        )
        report["line_count_runtime_probe"]["natural_h2_path_reachability"] = (
            "not claimed; the existing H2 scenario uses selector 6 and does not naturally enter this helper"
        )
        report["line_count_runtime_probe"]["original_invocation"] = report.get("original_run", {}).get(
            "direct_line_count_runtime_probe", [])
        report["line_count_runtime_probe"]["patched_invocation"] = report.get("patched_run", {}).get(
            "direct_line_count_runtime_probe", [])
        report["runtime_composition_manifest_sha256"] = sha(
            (COMPOSED / "manifest.json").read_bytes()
        )
        report["runtime_probe_wrapper_path"] = str(Path(__file__).resolve())
        report["runtime_probe_wrapper_sha256"] = sha(Path(__file__).read_bytes())
        report["passed"] = bool(report.get("passed"))
        report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(f"LINE-COUNT RUNTIME REPORT {report_path} SHA256 {sha(report_path.read_bytes())}")
    print(f"COMPOSED IMAGE {manifest['new_cumulative_image_sha256']} IPS {manifest['new_cumulative_ips_sha256']}")
    return status


if __name__ == "__main__":
    raise SystemExit(main())
