import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from tools.conditional_pair_experiment import (
    CALLERS, FUNCTIONS, ROOT, discover_bl_callers, run, verify_reference,
)


class TestConditionalPairExperiment(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image = (ROOT / "extracted/exefs/code.bin").read_bytes()
        cls.game = json.loads((ROOT / "config/game_info.json").read_text(encoding="utf-8"))
        with (ROOT / "config/functions.csv").open(encoding="utf-8", newline="") as stream:
            import csv
            cls.rows = list(csv.DictReader(stream))

    def test_pinned_bodies_and_direct_callers(self):
        verify_reference(self.image, self.game["code_sha256"], self.rows)
        callers = discover_bl_callers(self.image)
        self.assertEqual(callers, CALLERS)
        self.assertEqual(FUNCTIONS, {0x00110C2C: 0x1C, 0x00121150: 0x30})

    def test_hash_or_body_change_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            verify_reference(self.image, "0" * 64, self.rows)
        changed = bytearray(self.image)
        changed[0x00110C2C - 0x00100000] ^= 1
        with self.assertRaisesRegex(ValueError, "Original instructions changed"):
            verify_reference(bytes(changed), hashlib.sha256(changed).hexdigest(), self.rows)

    def test_differential_cases_controls_and_call_windows_on_two_seeds(self):
        for seed in (7, 20261024):
            with tempfile.TemporaryDirectory() as temporary:
                report = run(ROOT / "extracted/exefs/code.bin", Path(temporary),
                              samples=1, seed=seed)
            self.assertTrue(report["passed"], seed)
            self.assertEqual(len(report["functions"]), 2)
            self.assertTrue(all(row["passed"] for row in report["functions"]))
            self.assertEqual(sum(row["cases"] for row in report["functions"]), 14)
            self.assertEqual(len(report["negative_controls"]), 4)
            self.assertTrue(all(row["detected"] for row in report["negative_controls"]))
            self.assertEqual(len(report["caller_windows"]), 4)
            self.assertTrue(all(row["passed"] for row in report["caller_windows"]))


if __name__ == "__main__":
    unittest.main()
