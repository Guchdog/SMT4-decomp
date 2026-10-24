import unittest

from tools.title_transition_callback_00151404_experiment import ROOT, run_original_151404


class TestTitleTransitionCallback00151404Experiment(unittest.TestCase):
    def test_original_type1_callback_and_reached_callees_return_to_help(self):
        base = ROOT / "build/semantic-equivalence/real-assets"
        report = run_original_151404(
            (base / "exefs/code.bin").read_bytes(),
            (base / "romfs/title/TitleTable.tbb").read_bytes(),
        )
        self.assertTrue(report["passed"])
        self.assertEqual(report["callback_candidate"], "0x151404")
        self.assertEqual(report["callback"]["count"], 1)
        self.assertEqual(report["callback"]["entry"]["s0_bits"], "0x3f000000")
        self.assertEqual(report["callback"]["entry"]["s1_bits"], "0x3f800000")
        self.assertEqual(report["callback"]["entry"]["s2_bits"], "0x3f400000")
        self.assertEqual(report["callback"]["before_return"]["s0_bits"], "0x3f400000")
        self.assertEqual(report["callback"]["after_return"]["s0_bits"], "0x3f400000")
        self.assertEqual(report["callback"]["stack_writes"], [
            {"pc": "0x151404", "address": "0x8000ff0", "size": 4, "value": "0x2000a00"},
            {"pc": "0x151404", "address": "0x8000ff4", "size": 4, "value": "0x2872e8"},
            {"pc": "0x151408", "address": "0x8000fe0", "size": 8, "value": "0x3e8000003f400000"},
            {"pc": "0x151408", "address": "0x8000fe8", "size": 8, "value": "0x0"},
        ])
        self.assertEqual([row["target"] for row in report["reached_original_callees"]],
                         ["0x14d608", "0x15258c", "0x14d608"])
        self.assertEqual([row["target"] for row in report["direct_calls"]], [
            "0x2872a4", "0x14d608", "0x15258c", "0x20ffa0",
            "0x2c0ec4", "0x2ac2f4", "0x2c0e9c",
        ])
        self.assertEqual(report["final_state"]["nestedB_0x38"], 0.75)
        self.assertEqual(report["final_state"]["nestedB_0x3c"], 1.0)
        self.assertEqual(report["read_count"], 62)
        self.assertEqual(report["write_count"], 20)
        self.assertEqual(report["unexpected_reads"], [])
        self.assertEqual(report["stop_before_presentation"], "0x1ea15c")
        self.assertEqual(report["help_text"], "Start a new game from the beginning.")


if __name__ == "__main__":
    unittest.main()
