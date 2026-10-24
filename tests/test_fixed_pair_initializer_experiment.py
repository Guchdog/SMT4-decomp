import tempfile
import unittest
from pathlib import Path

from tools.fixed_pair_initializer_experiment import (
    CALLERS, OFFSETS, ROOT, run, verify_reference,
)
from tools.semantic_experiment_support import load_pinned_reference


class TestFixedPairInitializerExperiment(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pinned = load_pinned_reference(
            ROOT / "extracted/exefs/code.bin", ROOT / "config/game_info.json",
            ROOT / "config/functions.csv",
        )

    def test_shapes_and_callers(self):
        rows = verify_reference(self.pinned.image, self.pinned.ledger)
        self.assertEqual(OFFSETS, {0x00399D4C: 4, 0x003ABCF4: 0x14})
        self.assertEqual(CALLERS[0x00399D4C], (0x001924DC, 0x00276C04))
        self.assertEqual(CALLERS[0x003ABCF4], ())
        self.assertEqual(len(rows), len(self.pinned.ledger))

    def test_two_seeds_and_negative_controls(self):
        for seed in (7, 20261024):
            with tempfile.TemporaryDirectory() as temporary:
                report = run(ROOT / "extracted/exefs/code.bin", Path(temporary),
                             samples=1, seed=seed)
            self.assertTrue(report["passed"], seed)
            self.assertEqual(sum(item["cases"] for item in report["functions"]), 8)
            self.assertEqual(len(report["direct_caller_windows"]), 2)
            self.assertTrue(all(item["passed"] for item in report["direct_caller_windows"]))
            self.assertEqual(len(report["negative_controls"]), 3)
            self.assertTrue(all(item["detected"] for item in report["negative_controls"]))


if __name__ == "__main__":
    unittest.main()
