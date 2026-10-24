import unittest

from tools.title_transition_mutator_experiment import ROOT, run_mutator


class TestTitleTransitionMutatorExperiment(unittest.TestCase):
    def test_continuous_original_arm_executes_transition_mutations(self):
        report = run_mutator(
            (ROOT / "extracted/exefs/code.bin").read_bytes(),
            (ROOT / "build/semantic-equivalence/real-assets/romfs/title/TitleTable.tbb").read_bytes(),
        )
        self.assertTrue(report["passed"])
        self.assertEqual(report["help_entry"], "0x1ea12c")
        self.assertEqual(report["stop_before_presentation"], "0x1ea15c")
        self.assertEqual(report["presentation_callee_not_entered"], "0x29f10c")
        self.assertEqual(report["help_text"], "Start a new game from the beginning.")
        self.assertTrue(all(report["reached"].values()))
        self.assertEqual(report["read_count"], 38)
        self.assertEqual(report["write_count"], 6)
        self.assertEqual(
            [(row["pc"], row["address"], row["size"], row["value"])
             for row in report["writes"]],
            [("0x1ea0b0", "0x2000300", 4, "0x6"),
             ("0x1ea0bc", "0x20009f6", 1, "0x0"),
             ("0x1ea0c0", "0x2000198", 4, "0x3f400000"),
             ("0x1ea0ec", "0x2000340", 4, "0x0"),
             ("0x1ea0f8", "0x2000bf6", 1, "0x1"),
             ("0x1ea128", "0x2000194", 1, "0x1")],
        )
        self.assertEqual(report["read_count"], 38)
        self.assertEqual(report["final_state"], {
            "handle_a_flags": 6,
            "handle_b_flags": 0,
            "work_0x94": 1,
            "work_0x98": 0.75,
            "nested_a_0x1f6": 0,
            "nested_b_0x1f6": 1,
        })
        self.assertEqual(report["write_count"], 6)
        self.assertEqual([row["target"] for row in report["call_entries"]],
                         ["0x25a274", "0x2d569c", "0x2872a4", "0x20ffa0",
                          "0x2c0ec4", "0x2ac2f4", "0x2c0e9c"])


if __name__ == "__main__":
    unittest.main()
