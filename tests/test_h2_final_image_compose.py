"""Focused deterministic tests for the H2 final-image compositor."""
from __future__ import annotations

import json
from pathlib import Path
import unittest

from tools.h2_calc_code_patch import apply_ips
from tools.h2_final_image_compose import (
    CALLBACK_DIR, CALLBACK_SHA256, FILL_DIR, FILL_SHA256, MAPPER_DIR,
    MAPPER_SHA256, ORIGINAL, ORIGINAL_SHA256, compose_images, contiguous_records,
    sha256,
)


class FinalImageComposeTests(unittest.TestCase):
    def test_three_reviewed_inputs_compose_to_pinned_image(self):
        original = ORIGINAL.read_bytes()
        callback = (CALLBACK_DIR / "code.combined.bin").read_bytes()
        mapper = (MAPPER_DIR / "code.h2-mappers.bin").read_bytes()
        fill = (FILL_DIR / "code.h2-fill-pair.bin").read_bytes()
        manifests = [json.loads(path.read_text(encoding="utf-8")) for path in (
            CALLBACK_DIR / "manifest.json", MAPPER_DIR / "manifest.json", FILL_DIR / "manifest.json")]
        final, ips, manifest = compose_images(original, callback, mapper, fill, *manifests)
        self.assertEqual(sha256(original), ORIGINAL_SHA256)
        self.assertEqual(sha256(callback), CALLBACK_SHA256)
        self.assertEqual(sha256(mapper), MAPPER_SHA256)
        self.assertEqual(sha256(fill), FILL_SHA256)
        self.assertEqual(sha256(final), "acd8b2f35df08f225ca65b0fbf8aeef2dbbaa71171904e31c301e8bff6a51446")
        self.assertEqual(apply_ips(original, ips), final)
        self.assertTrue(manifest["composition"]["copy_pair"]["preserved"])

    def test_ips_records_are_contiguous_and_nonempty(self):
        before = b"0123456789"
        after = b"01XY456Z89"
        records = contiguous_records(before, after)
        self.assertEqual(records, [(2, b"XY"), (7, b"Z")])

    def test_wrong_source_image_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "pinned original"):
            compose_images(b"x", b"x", b"x", b"x", {}, {}, {})


if __name__ == "__main__":
    unittest.main()
