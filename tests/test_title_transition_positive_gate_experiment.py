import unittest

from tools.title_transition_positive_gate_experiment import ROOT, run_positive_gate


class TestTitleTransitionPositiveGateExperiment(unittest.TestCase):
    def test_original_positive_fade_gate_and_synthetic_callback_reach_help(self):
        base = ROOT / "build/semantic-equivalence/real-assets"
        report = run_positive_gate(
            (base / "exefs/code.bin").read_bytes(),
            (base / "romfs/title/TitleTable.tbb").read_bytes(),
        )
        self.assertTrue(report["passed"])
        self.assertTrue(all(report["reached"].values()))
        self.assertEqual(report["help_entry"], "0x1ea12c")
        self.assertEqual(report["stop_before_presentation"], "0x1ea15c")
        self.assertEqual(report["presentation_callee_not_entered"], "0x29f10c")
        self.assertEqual(report["help_text"], "Start a new game from the beginning.")
        self.assertEqual(report["callback"]["count"], 1)
        self.assertEqual(report["callback"]["input"]["r0_object"], "0x2000c00")
        self.assertEqual(report["callback"]["input"]["r1_callback"], "0x1000100")
        self.assertEqual(report["callback"]["input"]["s0_bits"], "0x3f000000")
        self.assertEqual(report["callback"]["input"]["s2_bits"], "0x3f400000")
        self.assertEqual(report["callback"]["memory_writes"], [])
        self.assertEqual(report["write_count"], 11)
        self.assertEqual(report["final_state"], {
            "handle_a_flags": 6,
            "handle_b_flags": 0,
            "work_0x94": 1,
            "work_0x98": 0.75,
            "callback_nested_0x38": 0.5,
            "callback_nested_0x3c": 1.0,
            "callback_nested_0x58": 1,
        })


if __name__ == "__main__":
    unittest.main()
