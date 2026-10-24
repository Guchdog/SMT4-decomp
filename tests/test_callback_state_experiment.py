from pathlib import Path
import tempfile
import unittest

from tools.callback_state_experiment import (
    DIRECT_CALLERS, FAULT_LABELS, FUNCTIONS, make_cases, run,
    verify_reference,
)
from tools.semantic_experiment_support import load_pinned_reference

ROOT = Path(__file__).resolve().parents[1]


class CallbackStateExperimentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reference = load_pinned_reference(
            ROOT / "extracted/exefs/code.bin", ROOT / "config/game_info.json",
            ROOT / "config/functions.csv",
        )

    def test_pins_both_identical_twenty_byte_leaves_and_no_direct_callers(self):
        evidence = verify_reference(self.reference)
        self.assertEqual(set(DIRECT_CALLERS), set(FUNCTIONS))
        self.assertTrue(all(not sites for sites in DIRECT_CALLERS.values()))
        self.assertIn("Indirect callback/table references were not resolved",
                      evidence["caller_review"])
        self.assertEqual({row["size"] for row in evidence["functions"].values()}, {20})
        self.assertEqual(
            {row["instructions"][3] for row in evidence["functions"].values()},
            {"stm r1, {r0, r2}"},
        )

    def test_cases_cover_aliasing_and_the_three_fault_boundaries(self):
        labels = [case.label for case in make_cases(0x003E89D8, 17, 3)]
        self.assertIn("source-aliases-first-store", labels)
        self.assertIn("source-aliases-second-store", labels)
        for label in FAULT_LABELS:
            self.assertIn(label, labels)

    def test_differential_state_faults_and_negative_controls(self):
        with tempfile.TemporaryDirectory(prefix="callback-state-test-") as temp:
            report = run(ROOT / "extracted/exefs/code.bin", Path(temp), 20261024, 4)
        self.assertTrue(report["passed"])
        self.assertEqual(len(report["functions"]), 2)
        self.assertEqual([row["cases"] for row in report["functions"]], [14, 14])
        self.assertTrue(all(row["passed"] for row in report["functions"]))
        for row in report["functions"]:
            self.assertEqual(len(row["fault_cases"]), 3)
            partial = row["partial_second_store_fault"]
            self.assertTrue(partial["passed"])
            self.assertEqual(partial["original_first_word"], 1)
            self.assertEqual(partial["candidate_first_word"], 1)
            self.assertNotEqual(row["fault_cases"][0]["original_fault_pc"],
                                row["fault_cases"][0]["candidate_fault_pc"])
        self.assertTrue(all(row["detected"] for row in report["negative_controls"]))
        order_controls = [row for row in report["negative_controls"]
                          if row["control"] == "wrong_store_order"]
        self.assertTrue(all(row["memory_effect_detected"] for row in order_controls))
        self.assertEqual(report["caller_windows"], [])


if __name__ == "__main__":
    unittest.main()
