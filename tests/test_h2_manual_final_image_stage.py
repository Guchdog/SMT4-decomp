from __future__ import annotations

import tempfile
import unittest
import hashlib
import json
from pathlib import Path
from unittest.mock import patch

from tools import h2_manual_final_image_stage as stage_tool
from tools.h2_manual_final_image_stage import (
    OUTPUT_ROOT,
    PINNED_MANIFEST_SHA256,
    _resolve_expected_manifest_sha256,
    _validate_integration_manifest,
    _verify_declared_record_coverage,
    compose,
    stage,
)
from tools.h2_calc_code_patch import apply_ips


class FinalImageStageTests(unittest.TestCase):
    def test_compose_roundtrip_split_and_ips_eof_marker(self) -> None:
        original = bytes(0x454F48 + 70_000)
        final = bytearray(original)
        final[1:70_000] = b"x" * 69_999
        final[0x454F46] = 0x7f
        final[-1] = 1
        ips, records = compose(original, bytes(final))
        self.assertGreater(len(records), 1)
        self.assertEqual(apply_ips(original, ips), bytes(final))

    def test_compose_rejects_size_change(self) -> None:
        with self.assertRaisesRegex(ValueError, "sizes differ"):
            compose(b"a", b"ab")

    def test_rejects_out_of_root_before_reading_inputs(self) -> None:
        with self.assertRaisesRegex(ValueError, "child directory"):
            stage(image_path=Path("missing"), expected_image_sha256="0" * 64,
                  manifest_path=Path("missing"), original_path=Path("missing"),
                  cci_path=Path("missing"), executable_path=Path("missing"),
                  seed_path=Path("missing"), output=Path(tempfile.gettempdir()) / "unsafe")

    def test_rejects_wrong_expected_image_hash_before_creating_output(self) -> None:
        OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=OUTPUT_ROOT) as temp:
            root = Path(temp)
            image = root / "image.bin"
            image.write_bytes(b"candidate")
            manifest = root / "manifest.json"
            manifest.write_text("{}", encoding="utf-8")
            original = root / "original.bin"
            original.write_bytes(b"original")
            output = root / "package"
            with self.assertRaisesRegex(ValueError, "final image SHA-256 mismatch"):
                stage(image_path=image, expected_image_sha256="0" * 64,
                      manifest_path=manifest, original_path=original, cci_path=root / "missing.cci",
                      executable_path=root / "missing.exe", seed_path=root / "missing-seed",
                      output=output)
            self.assertFalse(output.exists())

    def test_rejects_wrong_manifest_identity_before_creating_output(self) -> None:
        OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=OUTPUT_ROOT) as temp:
            root = Path(temp)
            image = root / "image.bin"
            image.write_bytes(b"candidate")
            manifest = root / "manifest.json"
            manifest.write_text('{"schema":1}', encoding="utf-8")
            original = root / "original.bin"
            original.write_bytes(b"original")
            output = root / "package"
            with self.assertRaisesRegex(ValueError, "manifest SHA-256"):
                stage(image_path=image, expected_image_sha256=hashlib.sha256(b"candidate").hexdigest(),
                    manifest_path=manifest, original_path=original, cci_path=root / "missing.cci",
                    executable_path=root / "missing.exe", seed_path=root / "missing-seed",
                    output=output)
            self.assertFalse(output.exists())

    def test_default_manifest_pin_is_preserved_and_used(self) -> None:
        self.assertEqual(
            PINNED_MANIFEST_SHA256,
            "4002ab29da801d36eafd17fd728d0473f50d7d10ec6c786ba3135b6b431140cf",
        )
        self.assertEqual(_resolve_expected_manifest_sha256(None), PINNED_MANIFEST_SHA256)
        with tempfile.TemporaryDirectory() as temp:
            manifest = Path(temp) / "manifest.json"
            payload = json.dumps({
                "schema": 1,
                "patched_sha256": "a" * 64,
                "original_sha256": "b" * 64,
            }).encode()
            manifest.write_bytes(payload)
            # Exercise the same default-resolution path with a temporary approved pin.
            with patch.object(stage_tool, "PINNED_MANIFEST_SHA256", hashlib.sha256(payload).hexdigest()):
                integration, actual_hash = _validate_integration_manifest(
                    manifest,
                    expected_manifest_sha256=None,
                    final_hash="a" * 64,
                    original_hash="b" * 64,
                )
            self.assertEqual(integration["schema"], 1)
            self.assertEqual(actual_hash, hashlib.sha256(payload).hexdigest())

    def test_accepts_explicit_custom_manifest_hash(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            manifest = Path(temp) / "custom-manifest.json"
            payload = json.dumps({
                "schema": 1,
                "patched_sha256": "c" * 64,
                "original_sha256": "d" * 64,
            }).encode()
            manifest.write_bytes(payload)
            expected = hashlib.sha256(payload).hexdigest()
            integration, actual_hash = _validate_integration_manifest(
                manifest,
                expected_manifest_sha256=expected,
                final_hash="c" * 64,
                original_hash="d" * 64,
            )
            self.assertEqual(integration["patched_sha256"], "c" * 64)
            self.assertEqual(actual_hash, expected)

    def test_rejects_wrong_explicit_manifest_hash(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            manifest = Path(temp) / "wrong-hash-manifest.json"
            payload = json.dumps({
                "schema": 1,
                "patched_sha256": "e" * 64,
                "original_sha256": "f" * 64,
            }).encode()
            manifest.write_bytes(payload)
            with self.assertRaisesRegex(ValueError, "integration manifest SHA-256 mismatch"):
                _validate_integration_manifest(
                    manifest,
                    expected_manifest_sha256="0" * 64,
                    final_hash="e" * 64,
                    original_hash="f" * 64,
                )

    def test_declared_record_coverage_and_undeclared_change(self) -> None:
        original = b"abcdefgh"
        image = b"abXdeYgh"
        records = [
            {"offset": "0x2", "length": 1, "sha256": hashlib.sha256(b"X").hexdigest()},
            {"offset": "0x5", "length": 1, "sha256": hashlib.sha256(b"Y").hexdigest()},
        ]
        self.assertEqual(_verify_declared_record_coverage(original, image, records), 2)
        with self.assertRaisesRegex(ValueError, "undeclared change at 0x2"):
            _verify_declared_record_coverage(original, image, records[1:])

    def test_rejects_overlapping_records_before_checking_payload_hash(self) -> None:
        original = b"abcdefgh"
        image = b"abXdeYgh"
        records = [
            {"offset": "0x1", "length": 2,
             "sha256": hashlib.sha256(image[1:3]).hexdigest()},
            # This record overlaps the first one and intentionally has a wrong
            # payload hash to prove overlap validation happens before hashing.
            {"offset": "0x2", "length": 4, "sha256": "0" * 64},
        ]
        with self.assertRaisesRegex(ValueError, "IPS records overlap"):
            _verify_declared_record_coverage(original, image, records)

    def test_touching_ordered_records_are_allowed(self) -> None:
        original = b"abcdefgh"
        image = b"abXYefgh"
        records = [
            {"offset": "0x2", "length": 1,
             "sha256": hashlib.sha256(image[2:3]).hexdigest()},
            {"offset": "0x3", "length": 1,
             "sha256": hashlib.sha256(image[3:4]).hexdigest()},
        ]
        self.assertEqual(_verify_declared_record_coverage(original, image, records), 2)

    def test_large_ordered_record_set_uses_merged_coverage(self) -> None:
        original = bytes(4096)
        mutable = bytearray(original)
        records = []
        for offset in range(1, 2048, 2):
            mutable[offset] = 0xA5
            records.append({
                "offset": hex(offset),
                "length": 1,
                "sha256": hashlib.sha256(b"\xA5").hexdigest(),
            })
        self.assertEqual(len(records), 1024)
        self.assertEqual(_verify_declared_record_coverage(original, bytes(mutable), records), 1024)


if __name__ == "__main__":
    unittest.main()
