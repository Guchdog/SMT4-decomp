import tempfile
import unittest
from pathlib import Path

from tools.flag_initializer_experiment import TAGS, ROOT, run, verify_reference
from tools.semantic_experiment_support import load_pinned_reference


class TestFlagInitializerExperiment(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pinned = load_pinned_reference(
            ROOT / "extracted/exefs/code.bin", ROOT / "config/game_info.json",
            ROOT / "config/functions.csv",
        )

    def test_reference_instruction_bodies_and_caller_scan(self):
        rows, callers = verify_reference(self.pinned.image, self.pinned.ledger)
        self.assertEqual(TAGS, {0x00383780: 0x11, 0x003A1A6C: 0x13})
        self.assertEqual(len(rows), len(self.pinned.ledger))
        self.assertEqual(callers, {0x00383780: (), 0x003A1A6C: ()})

    def test_two_seeds_all_contract_checks_and_negative_controls(self):
        for seed in (7, 20261024):
            with tempfile.TemporaryDirectory() as temporary:
                report = run(ROOT / "extracted/exefs/code.bin", Path(temporary),
                             samples=8, seed=seed)
            self.assertTrue(report["passed"], seed)
            self.assertEqual(sum(item["cases"] for item in report["functions"]), 28)
            self.assertEqual(report["executed_direct_caller_windows"], [])
            self.assertEqual(len(report["negative_controls"]), 4)
            self.assertTrue(all(item["detected"] for item in report["negative_controls"]))
            self.assertTrue(all("NZCV" in item["checks"] for item in report["functions"]))


if __name__ == "__main__":
    unittest.main()
