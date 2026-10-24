import hashlib
import tempfile
import unittest
from pathlib import Path

from tools.record_init_and_progress_writer_experiment import (
    INIT_ADDRESS, PROGRESS_ADDRESS, ROOT, SEEDS, run, verify_reference,
)
from tools.semantic_experiment_support import load_pinned_reference


class TestRecordInitAndProgressWriterExperiment(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pinned = load_pinned_reference(ROOT / "extracted/exefs/code.bin",
                                       ROOT / "config/game_info.json",
                                       ROOT / "config/functions.csv")
        cls.image, cls.game_info, cls.ledger = pinned.image, pinned.game_info, pinned.ledger

    def test_reference_bodies_and_hash_pin(self):
        report = verify_reference(self.image, self.game_info, self.ledger)
        self.assertEqual({int(x, 16) for x in report["functions"]},
                         {INIT_ADDRESS, PROGRESS_ADDRESS})
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            verify_reference(self.image, {**self.game_info, "code_sha256": "0" * 64}, self.ledger)
        changed = bytearray(self.image)
        changed[INIT_ADDRESS - 0x00100000] ^= 1
        with self.assertRaisesRegex(ValueError, "reference instructions changed"):
            verify_reference(bytes(changed),
                             {**self.game_info,
                              "code_sha256": hashlib.sha256(changed).hexdigest()}, self.ledger)

    def test_two_seed_differential_aliasing_and_controls(self):
        for seed in SEEDS:
            with tempfile.TemporaryDirectory() as temporary:
                report = run(ROOT / "extracted/exefs/code.bin", Path(temporary), seed)
            self.assertTrue(report["passed"], seed)
            self.assertEqual(report["functions"][0]["cases"], 64)
            self.assertEqual(report["functions"][1]["cases"], 64)
            self.assertEqual(report["functions"][1]["alias_cases"], 4)
            self.assertTrue(all(item["passed"] for item in report["functions"]))
            self.assertEqual(len(report["negative_controls"]), 4)
            self.assertTrue(all(item["detected"] for item in report["negative_controls"]))


if __name__ == "__main__":
    unittest.main()
