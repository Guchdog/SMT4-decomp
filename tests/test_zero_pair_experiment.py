import tempfile
import unittest
from pathlib import Path

from tools.zero_pair_experiment import (
    CALLBACK_SITES, DIRECT_CALLERS, ROOT, TARGETS, run, verify_reference,
)
from tools.semantic_experiment_support import load_pinned_reference


class TestZeroPairExperiment(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pinned = load_pinned_reference(
            ROOT / "extracted/exefs/code.bin", ROOT / "config/game_info.json",
            ROOT / "config/functions.csv",
        )

    def test_instruction_shapes_and_reference_evidence(self):
        rows = verify_reference(self.pinned.image, self.pinned.ledger)
        self.assertEqual(tuple(TARGETS), (0x0011B850, 0x0017F5E8, 0x0017F5F8))
        self.assertEqual(DIRECT_CALLERS[0x0011B850], (0x00110D94, 0x0011109C))
        self.assertEqual(len(CALLBACK_SITES[0x0017F5E8]), 2)
        self.assertEqual(len(CALLBACK_SITES[0x0017F5F8]), 1)
        self.assertEqual(len(rows), len(self.pinned.ledger))

    def test_pinned_reference_rejects_mutation(self):
        with tempfile.TemporaryDirectory() as temporary:
            bad_image = Path(temporary) / "code.bin"
            changed = bytearray(self.pinned.image)
            changed[0] ^= 1
            bad_image.write_bytes(changed)
            with self.assertRaisesRegex(ValueError, "SHA-256"):
                load_pinned_reference(bad_image, ROOT / "config/game_info.json",
                                      ROOT / "config/functions.csv")

    def test_candidates_and_controls_with_two_seeds(self):
        for seed in (7, 20261024):
            with tempfile.TemporaryDirectory() as temporary:
                report = run(ROOT / "extracted/exefs/code.bin", Path(temporary),
                             samples=1, seed=seed)
            self.assertTrue(report["passed"], seed)
            self.assertEqual(sum(item["cases"] for item in report["functions"]), 12)
            self.assertEqual(len(report["direct_caller_windows"]), 2)
            self.assertTrue(all(item["passed"] for item in report["direct_caller_windows"]))
            self.assertEqual(len(report["negative_controls"]), 3)
            self.assertTrue(all(item["detected"] for item in report["negative_controls"]))


if __name__ == "__main__":
    unittest.main()
