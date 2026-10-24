import json
import hashlib
import tempfile
import unittest
from pathlib import Path

from tools.scalar_offset_experiment import ROOT, FUNCTIONS, run, verify_reference


class TestScalarOffsetExperiment(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image = (ROOT / "extracted/exefs/code.bin").read_bytes()
        cls.game = json.loads((ROOT / "config/game_info.json").read_text(encoding="utf-8"))
        with (ROOT / "config/functions.csv").open(encoding="utf-8", newline="") as stream:
            import csv
            cls.ledger = list(csv.DictReader(stream))

    def test_reference_bodies_are_the_pinned_two_add_shapes(self):
        verify_reference(self.image, self.game["code_sha256"], self.ledger)
        self.assertEqual(
            {function.address for function in FUNCTIONS},
            {0x00343550, 0x00343584, 0x00343590},
        )
        self.assertEqual([function.offset for function in FUNCTIONS], [0x5B4, 0xC04, 0x6FC])

    def test_wrong_hash_and_changed_original_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            verify_reference(self.image, "0" * 64, self.ledger)
        changed = bytearray(self.image)
        changed[FUNCTIONS[0].address - 0x00100000] ^= 1
        changed_bytes = bytes(changed)
        with self.assertRaisesRegex(ValueError, "instruction shape changed"):
            verify_reference(changed_bytes, hashlib.sha256(changed_bytes).hexdigest(), self.ledger)

    def test_all_candidates_and_controls(self):
        with tempfile.TemporaryDirectory() as temporary:
            report = run(ROOT / "extracted/exefs/code.bin", Path(temporary), samples=1, seed=7)
        self.assertTrue(report["passed"])
        self.assertEqual(len(report["functions"]), 3)
        self.assertTrue(all(function["passed"] for function in report["functions"]))
        self.assertEqual(sum(function["cases"] for function in report["functions"]), 27)
        self.assertEqual(len(report["negative_controls"]), 3)
        self.assertTrue(all(control["detected"] for control in report["negative_controls"]))


if __name__ == "__main__":
    unittest.main()
