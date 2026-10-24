import tempfile
import unittest
from pathlib import Path

from tools.script_vm_init_experiment import (
    ADDRESSES, EXPECTED_BYTES, EXPECTED_WRITE_EVENTS, ROOT, run, verify_reference,
)
from tools.semantic_experiment_support import load_pinned_reference


class TestScriptVmInitializerExperiment(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pinned = load_pinned_reference(
            ROOT / "extracted/exefs/code.bin", ROOT / "config/game_info.json",
            ROOT / "config/functions.csv",
        )

    def test_two_pinned_bodies_and_write_contract(self):
        rows = verify_reference(self.pinned.image, self.pinned.ledger)
        self.assertEqual(len(EXPECTED_BYTES), 60)
        self.assertEqual(len(rows), len(self.pinned.ledger))
        self.assertEqual(ADDRESSES, (0x00353124, 0x003531AC))
        self.assertEqual(EXPECTED_WRITE_EVENTS,
                         tuple((offset, 4) for offset in range(0, 0x28, 4))
                         + ((0x28, 1), (0x2C, 4), (0x30, 4)))

    def test_two_seed_differential_runs_and_negative_controls(self):
        for seed in (7, 20261024):
            with tempfile.TemporaryDirectory() as temporary:
                report = run(ROOT / "extracted/exefs/code.bin", Path(temporary),
                             samples=1, seed=seed)
            self.assertTrue(report["passed"], seed)
            self.assertEqual(sum(item["cases"] for item in report["functions"]), 8)
            self.assertTrue(all(item["ordered_write_width_trace"] == "verified"
                                for item in report["functions"]))
            self.assertEqual(report["manually_verified_caller_windows"], [])
            self.assertEqual(len(report["negative_controls"]), 3)
            self.assertTrue(all(item["detected"] for item in report["negative_controls"]))


if __name__ == "__main__":
    unittest.main()
