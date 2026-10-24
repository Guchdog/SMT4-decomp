import tempfile
import unittest
from pathlib import Path

from tools.group19_four_word_record_experiment import run
from tools.aoc_initializer_experiment import FUNCTIONS, ROOT


class TestGroup19FourWordRecordExperiment(unittest.TestCase):
    def test_two_seed_differential_and_negative_controls(self):
        with tempfile.TemporaryDirectory(prefix="smt4-group19-records-") as temp_dir:
            report = run(
                ROOT / "extracted/exefs/code.bin", Path(temp_dir),
                seeds=(20261024, 7), samples=4,
            )

        self.assertTrue(report["passed"])
        self.assertEqual(report["seeds"], [20261024, 7])
        self.assertEqual(len(report["runs"]), 2)
        self.assertEqual({int(item["address"], 16) for item in report["functions"]},
                         set(FUNCTIONS))
        self.assertTrue(all(item["passed_all_seeds"] for item in report["functions"]))
        self.assertTrue(all(not item["byte_identical"] for item in report["functions"]))
        for seed_report in report["runs"]:
            self.assertTrue(all(control["detected"] and
                                control["reason"] == "data memory differs"
                                for control in seed_report["negative_controls"]))

    def test_rejects_missing_or_repeated_seed(self):
        with tempfile.TemporaryDirectory(prefix="smt4-group19-invalid-seeds-") as temp_dir:
            with self.assertRaisesRegex(ValueError, "two distinct"):
                run(Path("unused"), Path(temp_dir), seeds=(7,), samples=0)
            with self.assertRaisesRegex(ValueError, "two distinct"):
                run(Path("unused"), Path(temp_dir), seeds=(7, 7), samples=0)


if __name__ == "__main__":
    unittest.main()
