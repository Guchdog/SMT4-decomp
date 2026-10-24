import unittest

from tools.title_transition_original_callback_experiment import ROOT, run_original_callback


class TestTitleTransitionOriginalCallbackExperiment(unittest.TestCase):
    def test_first_positive_gate_runs_real_15555c_clamp_callback(self):
        base = ROOT / "build/semantic-equivalence/real-assets"
        report = run_original_callback(
            (base / "exefs/code.bin").read_bytes(),
            (base / "romfs/title/TitleTable.tbb").read_bytes(),
        )
        self.assertTrue(report["passed"])
        self.assertEqual(report["callback_candidate"], "0x15555c")
        self.assertEqual(report["callback_instruction_pcs"], [
            "0x15555c", "0x155560", "0x155564", "0x155568", "0x15556c",
            "0x155570", "0x155574", "0x155578", "0x15557c", "0x155580",
        ])
        callback = report["callback"]
        self.assertEqual(callback["count"], 1)
        self.assertEqual(callback["entry"]["r1"], "0x15555c")
        self.assertEqual(callback["entry"]["s0_bits"], "0x3f000000")
        self.assertEqual(callback["entry"]["s1_bits"], "0x3f800000")
        self.assertEqual(callback["entry"]["s2_bits"], "0x3f400000")
        self.assertEqual(callback["at_return_instruction"]["s0_bits"], "0x3f400000")
        self.assertEqual(callback["after_return"]["s0_bits"], "0x3f400000")
        self.assertEqual(callback["at_return_instruction"]["s3_bits"], "0x3f000000")
        self.assertEqual(callback["memory_writes"], [])
        self.assertEqual(report["caller_clamped_value_s2"], 0.75)
        self.assertEqual(report["callback_output_s0"], 0.75)
        self.assertEqual(report["final_state"]["nestedB_0x38"], 0.75)
        self.assertEqual(report["final_state"]["nestedB_0x3c"], 1.0)
        self.assertEqual(report["read_count"], 50)
        self.assertEqual(report["write_count"], 11)
        self.assertEqual(report["unexpected_reads"], [])
        self.assertEqual(report["stop_before_presentation"], "0x1ea15c")
        self.assertEqual(report["help_text"], "Start a new game from the beginning.")


if __name__ == "__main__":
    unittest.main()
