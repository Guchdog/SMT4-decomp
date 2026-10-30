"""Stage a reviewed H2 code image into fresh, isolated Azahar profiles.

This tool only copies files and writes a mod IPS. It never launches Azahar or
reads/writes an installed Azahar user profile.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.h2_azahar_rsp_probe import PROFILE_SEED_FILES, ProbeError, file_manifest, sha256, stage_runtime
from tools.h2_calc_code_patch import apply_ips, encode_ips

PINNED_ORIGINAL_SHA256 = "1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558"
PINNED_MANIFEST_SHA256 = "4002ab29da801d36eafd17fd728d0473f50d7d10ec6c786ba3135b6b431140cf"
PINNED_CCI_SHA256 = "9cc760c2f37da9a4a3657e918e0eaebb3e8e80a91047e5c18f95aedf0242b4c2"
PINNED_AZAHAR_SHA256 = "c248414eb5328cb8bb720775ace6959898e2f50a0a10221c3a1e7a14190183eb"
OUTPUT_ROOT = Path("E:/SMT4decomp/build/h2-manual-comparison").resolve()
DEFAULT_IMAGE = ROOT / "build/agent-work/H2-semantic/h2-thumb-reintegrate-final-image/run-004/combined-build-final/code.combined.bin"
DEFAULT_MANIFEST = DEFAULT_IMAGE.with_name("manifest.json")
DEFAULT_ORIGINAL = ROOT / "extracted/exefs/code.bin"
DEFAULT_CCI = Path("E:/SMT4decomp/build/h2-runtime/h2-azahar-rsp-probe/run-007-59931/pinned-title.cci")
DEFAULT_EXE = Path("E:/emulador3ds/azahar.exe")
DEFAULT_SEED = ROOT / "build/h2-runtime/profile-pristine-user"
MOD_IPS_RELATIVE = Path("load/mods/00040000000E5C00/exefs/code.ips")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def compose(original: bytes, final: bytes) -> tuple[bytes, list[tuple[int, bytes]]]:
    """Make a standalone IPS and prove applying it reproduces ``final``."""
    if len(original) != len(final):
        raise ValueError("image sizes differ")
    records: list[tuple[int, bytes]] = []
    i = 0
    while i < len(original):
        if original[i] == final[i]:
            i += 1
            continue
        start = i
        # IPS reserves the byte sequence 'EOF' as its terminator.
        if start == 0x454F46:
            start -= 1
        i += 1
        while i < len(original) and original[i] != final[i] and i - start < 0xFFFF:
            i += 1
        records.append((start, final[start:i]))
    patch = encode_ips(records, len(original))
    if apply_ips(original, patch) != final:
        raise ValueError("standalone IPS roundtrip mismatch")
    return patch, records


def _require_hash(path: Path, expected: str, label: str) -> str:
    actual = sha256(path)
    if actual.lower() != expected.lower():
        raise ValueError(f"{label} SHA-256 mismatch: expected {expected}, got {actual}")
    return actual


def _resolve_expected_manifest_sha256(expected: str | None) -> str:
    """Use the reviewed run-004 pin unless a caller explicitly supplies one."""
    return PINNED_MANIFEST_SHA256 if expected is None else expected


def _validate_integration_manifest(manifest_path: Path, *, expected_manifest_sha256: str | None,
                                   final_hash: str, original_hash: str | None = None) -> tuple[dict, str]:
    manifest_bytes = manifest_path.read_bytes()
    manifest_hash = digest(manifest_bytes)
    expected = _resolve_expected_manifest_sha256(expected_manifest_sha256)
    if manifest_hash.lower() != expected.lower():
        raise ValueError(
            f"integration manifest SHA-256 mismatch: expected {expected}, got {manifest_hash}"
        )
    integration = json.loads(manifest_bytes)
    if integration.get("schema") != 1:
        raise ValueError("unsupported integration manifest schema")
    if integration.get("patched_sha256", "").lower() != final_hash.lower():
        raise ValueError("manifest final image identity does not match supplied image")
    if original_hash is not None and integration.get("original_sha256", "").lower() != original_hash.lower():
        raise ValueError("manifest original image identity does not match pinned original")
    return integration, manifest_hash


def _verify_declared_record_coverage(original: bytes, image: bytes,
                                     record_manifest: object) -> int:
    """Check final-image records and changed-byte coverage in one image sweep.

    The producer emits records ordered by file offset. Require that ordering,
    merge touching/overlapping spans as they are read, then advance one interval
    cursor while scanning the image. This is O(image bytes + record count),
    rather than checking every changed byte against every declared record.
    """
    if not isinstance(record_manifest, list) or not record_manifest:
        raise ValueError("integration manifest has no IPS record identity")
    intervals: list[tuple[int, int]] = []
    previous_offset = -1
    previous_end = -1
    for row in record_manifest:
        try:
            offset = int(row["offset"], 16)
            length = int(row["length"])
            expected_span_hash = str(row["sha256"]).lower()
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("integration manifest contains a malformed IPS record") from exc
        end = offset + length
        if offset < 0 or length <= 0 or end > len(image):
            raise ValueError("integration manifest IPS record is outside the code image")
        if offset < previous_offset:
            raise ValueError("integration manifest IPS records are not ordered by offset")
        if offset < previous_end:
            raise ValueError("integration manifest IPS records overlap")
        if digest(image[offset:end]) != expected_span_hash:
            raise ValueError(f"final image does not match manifest record at {offset:#x}")
        if intervals and offset <= intervals[-1][1]:
            intervals[-1] = (intervals[-1][0], max(intervals[-1][1], end))
        else:
            intervals.append((offset, end))
        previous_offset = offset
        previous_end = end

    interval_index = 0
    for offset, (before, after) in enumerate(zip(original, image)):
        while interval_index < len(intervals) and offset >= intervals[interval_index][1]:
            interval_index += 1
        if before != after and (interval_index == len(intervals)
                                or not intervals[interval_index][0] <= offset < intervals[interval_index][1]):
            raise ValueError(f"final image has undeclared change at {offset:#x}")
    return len(record_manifest)


def _validate_seed(seed: Path) -> list[dict]:
    seed = seed.resolve(strict=True)
    if not seed.is_dir():
        raise ValueError(f"profile seed is not a directory: {seed}")
    approved = sorted(p.as_posix() for p in PROFILE_SEED_FILES)
    missing = [relative for relative in approved if not (seed / Path(relative)).is_file()]
    if missing:
        raise ValueError(f"approved profile seed files are missing: {missing}")
    # The source seed may contain additional system files; stage_runtime copies
    # only this explicit allow-list into each new profile.
    return [{"path": relative, "sha256": sha256(seed / Path(relative)),
             "size": (seed / Path(relative)).stat().st_size} for relative in approved]


def _portable_config(user_root: Path) -> None:
    config = user_root / "config/qt-config.ini"
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(
        "[Debugging]\n"
        "use_gdbstub\\default=false\nuse_gdbstub=false\n"
        "enable_rpc_server\\default=false\nenable_rpc_server=false\n",
        encoding="utf-8",
        newline="\n",
    )


def stage(*, image_path: Path, expected_image_sha256: str, manifest_path: Path,
          original_path: Path, cci_path: Path, executable_path: Path, seed_path: Path,
          output: Path, expected_manifest_sha256: str | None = None) -> dict:
    out = output.resolve()
    if out == OUTPUT_ROOT or not out.is_relative_to(OUTPUT_ROOT):
        raise ValueError(f"output must be a child directory of {OUTPUT_ROOT}")
    if out.exists():
        raise ValueError(f"output directory already exists: {out}")

    image_path = image_path.resolve(strict=True)
    image = image_path.read_bytes()
    final_hash = digest(image)
    if final_hash.lower() != expected_image_sha256.lower():
        raise ValueError(f"final image SHA-256 mismatch: expected {expected_image_sha256}, got {final_hash}")
    manifest_path = manifest_path.resolve(strict=True)
    integration, manifest_hash = _validate_integration_manifest(
        manifest_path, expected_manifest_sha256=expected_manifest_sha256,
        final_hash=final_hash,
    )
    original_path = original_path.resolve(strict=True)
    original = original_path.read_bytes()
    original_hash = digest(original)
    if original_hash != PINNED_ORIGINAL_SHA256:
        raise ValueError("pinned original code.bin SHA-256 mismatch")
    if integration.get("original_sha256", "").lower() != original_hash:
        raise ValueError("manifest original image identity does not match pinned original")
    game_info = json.loads((ROOT / "config/game_info.json").read_text(encoding="utf-8"))
    if (len(original) != int(game_info["code_bin_size"])
            or game_info["code_sha256"].lower() != original_hash):
        raise ValueError("pinned original differs from config/game_info.json")
    cci_path = cci_path.resolve(strict=True)
    executable_path = executable_path.resolve(strict=True)
    seed_path = seed_path.resolve(strict=True)

    patch, records = compose(original, image)
    if apply_ips(original, patch) != image or digest(apply_ips(original, patch)) != final_hash:
        raise ValueError("standalone IPS application did not reproduce final image")
    record_count = _verify_declared_record_coverage(original, image, integration.get("ips_records"))
    _require_hash(cci_path, PINNED_CCI_SHA256, "pinned CCI")
    _require_hash(executable_path, PINNED_AZAHAR_SHA256, "pinned Azahar executable")
    seed_records = _validate_seed(seed_path)
    seed_before = file_manifest(seed_path)

    out.parent.mkdir(parents=True, exist_ok=True)
    out.mkdir()
    profiles = {}
    original_root = out / "original"
    staged_exe, staged_cci, _seed_rows, _assets, _runtime_files, _qt_conf = stage_runtime(
        executable_path, cci_path, seed_path, original_root, hardlink_game=True
    )
    _require_hash(staged_exe, PINNED_AZAHAR_SHA256, "staged Azahar executable")
    _require_hash(staged_cci, PINNED_CCI_SHA256, "staged CCI")
    # Keep exactly one common CCI in the package; both launch commands use it.
    staged_cci.unlink()
    original_user = original_root / "app/user"
    _portable_config(original_user)
    profiles["original"] = original_user
    patched_root = out / "patched"
    patched_root.mkdir()
    shutil.copytree(original_root / "app", patched_root / "app")
    profiles["patched"] = patched_root / "app/user"

    if file_manifest(profiles["original"]) != file_manifest(profiles["patched"]):
        raise ValueError("fresh original and patched profile seeds differ before patching")
    pristine_profiles = file_manifest(profiles["original"])
    ips_path = profiles["patched"] / MOD_IPS_RELATIVE
    ips_path.parent.mkdir(parents=True, exist_ok=True)
    ips_path.write_bytes(patch)
    if digest(ips_path.read_bytes()) != digest(patch):
        raise ValueError("staged IPS hash mismatch")
    if apply_ips(original, ips_path.read_bytes()) != image:
        raise ValueError("staged IPS application does not reproduce final image")
    patched_manifest = file_manifest(profiles["patched"])
    expected_patched = pristine_profiles + [{"path": MOD_IPS_RELATIVE.as_posix(),
                                               "size": len(patch), "sha256": digest(patch)}]
    if sorted(patched_manifest, key=lambda row: row["path"]) != sorted(expected_patched, key=lambda row: row["path"]):
        raise ValueError("original and patched profiles differ beyond the intended IPS")
    seed_after = file_manifest(seed_path)
    if seed_after != seed_before:
        raise ValueError("source seed changed while staging")

    # Both paths are on the approved E: staging volume. A hard link keeps the
    # pinned, immutable CCI available in this fresh package without allocating
    # another 1.75 GiB copy.
    os.link(cci_path, out / "pinned-title.cci")
    _require_hash(out / "pinned-title.cci", PINNED_CCI_SHA256, "staged shared CCI")
    launch_commands = {
        "original": [str((out / "original/app/azahar.exe").resolve()), str((out / "pinned-title.cci").resolve())],
        "patched": [str((out / "patched/app/azahar.exe").resolve()), str((out / "pinned-title.cci").resolve())],
    }
    result = {
        "schema": 1,
        "staging_only_runtime_not_run": True,
        "output": str(out),
        "original": {"path": str(original_path), "sha256": original_hash, "size": len(original)},
        "final_image": {"path": str(image_path), "sha256": final_hash, "size": len(image)},
        "integration_manifest": {"path": str(manifest_path), "sha256": manifest_hash},
        "standalone_ips": {"sha256": digest(patch), "size": len(patch), "record_count": len(records),
                           "manifest_record_count": record_count,
                           "changed_bytes": sum(a != b for a, b in zip(original, image)),
                           "profile_path": MOD_IPS_RELATIVE.as_posix()},
        "cci": {"path": str((out / "pinned-title.cci").resolve()), "sha256": sha256(out / "pinned-title.cci"),
                "source": str(cci_path), "storage": "hardlink"},
        "azahar": {"source": str(executable_path), "sha256": sha256(executable_path),
                   "profile_executables": {name: sha256(out / name / "app/azahar.exe") for name in profiles}},
        "seed": {"source": str(seed_path), "files": seed_records, "sha256": digest(json.dumps(seed_records, sort_keys=True).encode())},
        "profiles": {name: {"user_root": str(path.resolve()), "files": file_manifest(path),
                            "sha256": digest(json.dumps(file_manifest(path), sort_keys=True).encode())}
                      for name, path in profiles.items()},
        "profiles_differ_only_by_ips": True,
        "gdbstub_enabled": False,
        "rpc_server_enabled": False,
        "launch_commands": launch_commands,
        "launch_working_directories": {name: str((out / name / "app").resolve()) for name in profiles},
    }
    manifest_out = out / "staging-manifest.json"
    manifest_out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    result["staging_manifest"] = {"path": str(manifest_out.resolve()), "sha256": sha256(manifest_out)}
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", type=Path, default=DEFAULT_IMAGE)
    parser.add_argument("--expected-image-sha256", required=True)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--expected-manifest-sha256", default=None,
                        help="expected integration manifest SHA-256 (defaults to the reviewed run-004 pin)")
    parser.add_argument("--original", type=Path, default=DEFAULT_ORIGINAL)
    parser.add_argument("--cci", type=Path, default=DEFAULT_CCI)
    parser.add_argument("--azahar", type=Path, default=DEFAULT_EXE)
    parser.add_argument("--seed", type=Path, default=DEFAULT_SEED)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = stage(image_path=args.image, expected_image_sha256=args.expected_image_sha256,
                   manifest_path=args.manifest, original_path=args.original, cci_path=args.cci,
                   executable_path=args.azahar, seed_path=args.seed, output=args.output,
                   expected_manifest_sha256=args.expected_manifest_sha256)
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ProbeError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2)
