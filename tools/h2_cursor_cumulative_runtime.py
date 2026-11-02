"""Build an original-based H2 cursor IPS and run the paired autonomous Azahar scenario."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.h2_calc_code_patch import apply_ips, encode_ips

ORIGINAL = ROOT / "extracted/exefs/code.bin"
ORIGINAL_SHA = "1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558"
CUMULATIVE = ROOT / "build/agent-work/H2-semantic/h2-titleconfig-cursor-cumulative-closure/run001/results-002/code.h2-cursor-cumulative.bin"
CUMULATIVE_SHA = "aca919c95b0bc58af0a50b9f9f7f7d22084c2eb1dba5767889258920b08c582f"
BASE_AUDIT = ROOT / "build/agent-work/H2-semantic/h2-titleconfig-cursor-cumulative-closure/run001/results-002/interworking-base.json"
CANDIDATE_AUDIT = ROOT / "build/agent-work/H2-semantic/h2-titleconfig-cursor-cumulative-closure/run001/results-002/interworking-audit.json"
RUNNER = ROOT / "tools/h2_autonomous_gdb_verify.py"
DEFAULT_AZAHAR = ROOT / "build/agent-work/H2-semantic/h2-private-azahar-source/build-clang64/bin/Release/azahar.exe"
DEFAULT_GAME = Path("E:/emulador3ds/00040000000E5C00 Shin Megami Tensei IV (CTR-P-AMXE) (v0.1.0) (U).piratelegit-decrypted.cci")
DEFAULT_DLL_SOURCE = Path("E:/emulador3ds/azahar.exe")
DEFAULT_PROFILE = ROOT / "build/h2-runtime/profile-pristine-user"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def make_records(original: bytes, candidate: bytes) -> list[tuple[int, bytes]]:
    if len(original) != len(candidate):
        raise ValueError("the original and candidate code images must have identical sizes")
    records: list[tuple[int, bytes]] = []
    i = 0
    while i < len(original):
        if original[i] == candidate[i]:
            i += 1
            continue
        start = i
        payload = bytearray()
        while i < len(original) and original[i] != candidate[i] and len(payload) < 0xFFFF:
            payload.append(candidate[i])
            i += 1
        records.append((start, bytes(payload)))
    return records


def run(args: argparse.Namespace) -> dict:
    output = args.output_dir.resolve()
    if output.exists():
        raise FileExistsError(f"refusing to reuse output directory: {output}")
    output.mkdir(parents=True)
    image_dir = output / "image"
    image_dir.mkdir()
    original = ORIGINAL.read_bytes()
    candidate = CUMULATIVE.read_bytes()
    if sha(original) != ORIGINAL_SHA:
        raise ValueError("pinned original code.bin hash mismatch")
    if sha(candidate) != CUMULATIVE_SHA:
        raise ValueError("reviewed cumulative image hash mismatch")

    base_audit = json.loads(BASE_AUDIT.read_text(encoding="utf-8"))
    candidate_audit = json.loads(CANDIDATE_AUDIT.read_text(encoding="utf-8"))
    if base_audit.get("issues") != candidate_audit.get("issues"):
        raise ValueError("cumulative image changed whole-image interworking findings")
    if candidate_audit.get("unexpected_overlaps"):
        raise ValueError("interworking audit reports unexpected overlaps")
    if not candidate_audit.get("h2_helpers_preserved"):
        raise ValueError("H2 helper static checks failed")

    records = make_records(original, candidate)
    ips = encode_ips(records, len(original))
    if apply_ips(original, ips) != candidate:
        raise ValueError("original-based IPS roundtrip failed")
    image_path = image_dir / "code.h2-cursor-cumulative.bin"
    ips_path = image_dir / "code.h2-cursor-cumulative-original.ips"
    image_path.write_bytes(candidate)
    ips_path.write_bytes(ips)

    run_dir = output / "azahar-paired-run"
    command = [sys.executable, str(RUNNER), "--azahar", str(args.azahar.resolve(strict=True)),
               "--dll-source", str(args.dll_source.resolve(strict=True)), "--game", str(args.game.resolve(strict=True)),
               "--original-code", str(ORIGINAL), "--final-image", str(image_path),
               "--final-ips", str(ips_path), "--profile-seed", str(args.profile_seed.resolve(strict=True)),
               "--output-dir", str(run_dir), "--base-port", str(args.base_port),
               "--startup-timeout", str(args.startup_timeout), "--packet-timeout", str(args.packet_timeout)]
    proc = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
    runtime_report_path = run_dir / "autonomous-gdb-verification.json"
    runtime = json.loads(runtime_report_path.read_text(encoding="utf-8")) if runtime_report_path.is_file() else None
    report = {
        "schema": 1,
        "scope": "paired autonomous H2 TitleConfig scenario on original versus reviewed cumulative cursor image",
        "original_sha256": sha(original), "cumulative_sha256": sha(candidate),
        "original_based_ips_sha256": sha(ips), "ips_record_count": len(records),
        "changed_byte_count": sum(len(data) for _, data in records),
        "ips_roundtrip": True,
        "static_audit_findings_unchanged": True,
        "static_candidate_audit_passed": False,
        "static_audit_notes": candidate_audit.get("issues", []),
        "runner_sha256": sha(RUNNER.read_bytes()),
        "command": command,
        "runner_exit_code": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "runtime_report": str(runtime_report_path.resolve()) if runtime is not None else None,
        "runtime_report_sha256": sha(runtime_report_path.read_bytes()) if runtime_report_path.is_file() else None,
        "runtime_summary": None if runtime is None else {
            key: runtime.get(key) for key in (
                "paired_behavior_matched", "paired_scripted_behavior_matched",
                "paired_h2_lifecycle_behavior_matched", "readiness_completed_original",
                "readiness_completed_patched", "restart_persistence_outcome_matches_original",
                "profile_seed_unchanged", "runtime_support_assets_unchanged",
                "private_azahar_unchanged", "scripted_action_count", "checkpoint_count",
                "passed_checkpoint_count", "base_port", "private_azahar_sha256",
                "final_image_sha256", "final_ips_sha256", "cci_sha256",
            )
        },
        "limits": [
            "This is one defined scripted H2 TitleConfig scenario; it does not cover all natural cursor inputs or arbitrary task scheduling.",
            "The paired scenario does not observe every 0x0027FBC8 output write. It cannot prove the no-write axis sample path unreachable.",
            "The two inherited H8 ARM-to-Thumb issues remain in the aggregate static audit; neither was added by this image.",
            "A runtime pass here is not whole-game equivalence or proof of physical input mapping.",
        ],
    }
    (output / "runtime-report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"runner_exit_code": proc.returncode,
                      "runtime_report": str(runtime_report_path),
                      "runtime_summary": report["runtime_summary"],
                      "ips_sha256": report["original_based_ips_sha256"]}, indent=2))
    return report


def summarize_existing(runtime_dir: Path, report_dir: Path) -> dict:
    """Persist a completed short-path Azahar run without launching it again."""
    runtime_dir = runtime_dir.resolve(strict=True)
    report_dir = report_dir.resolve(strict=True)
    run_dir = runtime_dir / "azahar-paired-run"
    source_report = run_dir / "autonomous-gdb-verification.json"
    if not source_report.is_file():
        raise FileNotFoundError(source_report)
    runtime = json.loads(source_report.read_text(encoding="utf-8"))
    image_dir = runtime_dir / "image"
    dest_image_dir = report_dir / "image"
    dest_image_dir.mkdir(exist_ok=True)
    copied = []
    for name in ("code.h2-cursor-cumulative.bin", "code.h2-cursor-cumulative-original.ips"):
        src = image_dir / name
        dst = dest_image_dir / name
        shutil.copy2(src, dst)
        copied.append({"path": str(dst.relative_to(ROOT)), "sha256": sha(dst.read_bytes())})
    persisted_runtime = report_dir / "autonomous-gdb-verification.json"
    shutil.copy2(source_report, persisted_runtime)
    original = ORIGINAL.read_bytes()
    candidate = CUMULATIVE.read_bytes()
    ips = (image_dir / "code.h2-cursor-cumulative-original.ips").read_bytes()
    records = make_records(original, candidate)
    report = {
        "schema": 1,
        "scope": "paired autonomous H2 TitleConfig scenario on original versus reviewed cumulative cursor image",
        "original_sha256": sha(original), "cumulative_sha256": sha(candidate),
        "original_based_ips_sha256": sha(ips),
        "ips_record_count": len(records), "changed_byte_count": sum(len(data) for _, data in records),
        "ips_roundtrip": apply_ips(original, ips) == candidate,
        "static_audit_findings_unchanged": True,
        "static_candidate_audit_passed": False,
        "static_audit_notes": json.loads(CANDIDATE_AUDIT.read_text(encoding="utf-8")).get("issues", []),
        "runner_sha256": runtime.get("runner_sha256"),
        "runtime_report": str(persisted_runtime.relative_to(ROOT)),
        "runtime_report_sha256": sha(persisted_runtime.read_bytes()),
        "runtime_summary": {
            "passed": runtime.get("passed"),
            "paired_scripted_behavior_matched": runtime.get("paired_scripted_behavior_matched"),
            "paired_h2_lifecycle_behavior_matched": runtime.get("controlled_lifecycle", {}).get("paired_lifecycle_behavior_matched"),
            "readiness_completed_original": runtime.get("controlled_lifecycle", {}).get("readiness_completed_original"),
            "readiness_completed_patched": runtime.get("controlled_lifecycle", {}).get("readiness_completed_patched"),
            "restart_persistence_outcome_matches_original": runtime.get("restart_persistence_outcome_matches_original"),
            "profile_seed_unchanged": runtime.get("profile_seed_unchanged"),
            "runtime_support_assets_unchanged": runtime.get("runtime_support_assets_unchanged"),
            "private_azahar_unchanged": runtime.get("private_azahar_unchanged"),
            "scripted_action_count": runtime.get("scripted_action_count"),
            "checkpoint_count": len(runtime.get("checkpoint_comparisons", [])),
            "passed_checkpoint_count": sum(1 for row in runtime.get("checkpoint_comparisons", []) if row.get("passed")),
            "base_port": runtime.get("base_port"),
            "private_azahar_sha256": runtime.get("private_azahar_sha256"),
            "final_image_sha256": runtime.get("final_image_sha256"),
            "final_ips_sha256": runtime.get("final_ips_sha256"),
            "cci_sha256": runtime.get("cci_sha256"),
        },
        "artifacts": copied,
        "limitations": [
            "This is one defined scripted H2 TitleConfig scenario; it does not cover all natural cursor inputs or arbitrary task scheduling.",
            "The paired scenario does not observe every 0x0027FBC8 output write. It cannot prove the no-write axis sample path unreachable.",
            "The two inherited H8 ARM-to-Thumb issues remain in the aggregate static audit; neither was added by this image.",
            "A runtime pass here is not whole-game equivalence or proof of physical input mapping.",
        ],
    }
    (report_dir / "runtime-report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--summarize-existing", type=Path)
    parser.add_argument("--report-dir", type=Path)
    parser.add_argument("--azahar", type=Path, default=DEFAULT_AZAHAR)
    parser.add_argument("--dll-source", type=Path, default=DEFAULT_DLL_SOURCE)
    parser.add_argument("--game", type=Path, default=DEFAULT_GAME)
    parser.add_argument("--profile-seed", type=Path, default=DEFAULT_PROFILE)
    parser.add_argument("--base-port", type=int, default=60340)
    parser.add_argument("--startup-timeout", type=float, default=60)
    parser.add_argument("--packet-timeout", type=float, default=300)
    args = parser.parse_args()
    if args.summarize_existing:
        if not args.report_dir:
            parser.error("--summarize-existing requires --report-dir")
        report = summarize_existing(args.summarize_existing, args.report_dir)
        print(json.dumps({"runtime_summary": report["runtime_summary"],
                          "runtime_report_sha256": report["runtime_report_sha256"],
                          "ips_sha256": report["original_based_ips_sha256"]}, indent=2))
        return 0 if report["runtime_summary"].get("passed") else 1
    if not args.output_dir:
        parser.error("--output-dir is required unless --summarize-existing is used")
    report = run(args)
    return report["runner_exit_code"]


if __name__ == "__main__":
    raise SystemExit(main())
