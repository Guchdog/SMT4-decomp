import unittest

from tools.title_second_gate_candidate_experiment import (
    CALLBACK_CLAMP,
    CALLBACK_TYPE1,
    ROOT,
    run_candidate,
)


class TestTitleSecondGateCandidateExperiment(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        base = ROOT / "build/semantic-equivalence/real-assets"
        cls.image = (base / "exefs/code.bin").read_bytes()
        cls.tbb = (base / "romfs/title/TitleTable.tbb").read_bytes()

    def test_default_type0_callback_candidate_in_second_gate(self):
        report = run_candidate(self.image, self.tbb, CALLBACK_CLAMP)
        self.assertTrue(report["passed"])
        self.assertEqual(report["callback_selection"],
                         "explicit synthetic record pointer; live title selection unknown")
        self.assertEqual(report["second_gate_call_pc"], "0x210010")
        self.assertEqual(report["callback_candidate"], "0x15555c")
        self.assertEqual(report["callback"]["count"], 1)
        self.assertEqual(report["callback"]["entry"]["lr"], "0x210014")
        self.assertEqual(report["callback"]["entry"]["s0_bits"], "0x3e800000")
        self.assertEqual(report["callback"]["entry"]["s1_bits"], "0x3f19999a")
        self.assertEqual(report["callback"]["entry"]["s2_bits"], "0x3f19999a")
        self.assertEqual(report["callback"]["return"]["s0_bits"], "0x3f19999a")
        self.assertEqual(report["callback_writes"], [])
        self.assertEqual(report["callback_callees_reached"], [])
        self.assertEqual(report["callback_instruction_pcs"], [
            "0x15555c", "0x155560", "0x155564", "0x155568", "0x15556c",
            "0x155570", "0x155574", "0x155578", "0x15557c", "0x155580",
        ])
        self.assertEqual(report["final_state"]["selected_record_0x38"], 0.6000000238418579)
        self.assertEqual(report["read_count"], 65)
        self.assertEqual(report["write_count"], 16)
        self.assertEqual(report["unexpected_reads"], [])
        self.assertEqual(report["stop_before_presentation"], "0x1ea15c")
        self.assertEqual(report["help_text"], "Start a new game from the beginning.")

    def test_type1_callback_candidate_in_second_gate(self):
        report = run_candidate(self.image, self.tbb, CALLBACK_TYPE1)
        self.assertTrue(report["passed"])
        self.assertEqual(report["callback_candidate"], "0x151404")
        self.assertEqual(report["callback"]["count"], 1)
        self.assertEqual(report["callback"]["entry"]["lr"], "0x210014")
        self.assertEqual(report["callback"]["entry"]["s0_bits"], "0x3e800000")
        self.assertEqual(report["callback"]["entry"]["s1_bits"], "0x3f19999a")
        self.assertEqual(report["callback"]["entry"]["s2_bits"], "0x3f19999a")
        self.assertEqual(report["callback"]["return"]["s0_bits"], "0x3e800000")
        self.assertEqual(report["callback_callees_reached"], ["0x14d608", "0x15258c"])
        self.assertEqual(report["final_state"]["selected_record_0x38"], 0.25)
        self.assertEqual(report["read_count"], 77)
        self.assertEqual(report["write_count"], 25)
        self.assertEqual(report["unexpected_reads"], [])
        self.assertEqual(report["stop_before_presentation"], "0x1ea15c")
        self.assertEqual(report["help_text"], "Start a new game from the beginning.")
        self.assertTrue(all(0x8000FC0 <= int(row["address"], 16) < 0x8001000
                            for row in report["callback_writes"]))
        self.assertTrue(all(0x8000FC0 <= int(row["address"], 16) < 0x8001000
                            for row in report["writes"]
                            if int(row["address"], 16) >= 0x8000000))

    def test_unknown_candidate_is_rejected_without_running(self):
        with self.assertRaises(ValueError):
            run_candidate(self.image, self.tbb, 0x01000120)


if __name__ == "__main__":
    unittest.main()
