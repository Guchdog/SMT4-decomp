import tempfile
import unittest
from pathlib import Path

from tools.semantic_experiment_support import load_pinned_reference
from tools.typed_constructor_experiment import (
    EXACT_BYTES, FUNCTIONS, ROOT, run, verify_reference,
)


class TestTypedConstructorExperiment(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pinned = load_pinned_reference(
            ROOT / "extracted/exefs/code.bin", ROOT / "config/game_info.json",
            ROOT / "config/functions.csv",
        )

    def test_exact_bodies_table_sites_and_direct_caller_scan(self):
        rows, callers = verify_reference(self.pinned.image, self.pinned.ledger)
        self.assertEqual(set(FUNCTIONS), {0x003A80CC, 0x003A9644})
        self.assertEqual(set(EXACT_BYTES), set(FUNCTIONS))
        self.assertEqual(callers, {address: () for address in FUNCTIONS})
        self.assertEqual(len(rows), len(self.pinned.ledger))

    def test_two_seed_differential_runs_and_negative_controls(self):
        total_cases = 0
        for seed in (7, 20261024):
            with tempfile.TemporaryDirectory() as temporary:
                report = run(ROOT / "extracted/exefs/code.bin", Path(temporary),
                             samples=64, seed=seed)
            self.assertTrue(report["passed"], seed)
            self.assertEqual(report["seed"], seed)
            self.assertEqual(len(report["functions"]), 2)
            self.assertEqual([item["cases"] for item in report["functions"]], [68, 68])
            self.assertTrue(all(item["flags_checked"] for item in report["functions"]))
            self.assertTrue(all(item["ordered_read_write_width_trace_checked"]
                                for item in report["functions"]))
            self.assertEqual(report["caller_windows"], [])
            self.assertEqual(len(report["negative_controls"]), 3)
            self.assertTrue(all(item["detected"] for item in report["negative_controls"]))
            self.assertTrue(any("partial data-abort/fault behavior" in item
                                for item in report["limitations"]))
            total_cases += sum(item["cases"] for item in report["functions"])
        self.assertEqual(total_cases, 272)


if __name__ == "__main__":
    unittest.main()
