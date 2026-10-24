import unittest

from tools.title_transition_second_positive_gate_experiment import ROOT, run_second_positive_gate


class TestTitleTransitionSecondPositiveGateExperiment(unittest.TestCase):
    def test_indexed_record_positive_gate_and_second_blx_reach_help(self):
        base = ROOT / "build/semantic-equivalence/real-assets"
        report = run_second_positive_gate(
            (base / "exefs/code.bin").read_bytes(),
            (base / "romfs/title/TitleTable.tbb").read_bytes(),
        )
        self.assertTrue(report["passed"])
        self.assertEqual(report["second_positive_body"], "0x20ffac")
        self.assertEqual(report["second_blx_pc"], "0x210010")
        self.assertEqual(report["stop_before_presentation"], "0x1ea15c")
        self.assertEqual(report["help_text"], "Start a new game from the beginning.")
        self.assertEqual(report["indexed_table"], {
            "descriptor": "0x2000a00",
            "descriptor_0x148": 1,
            "metadata": "0x2000c20",
            "stride": 1,
            "base": "0x2000c60",
            "index": 1,
            "selected_slot_address": "0x2000c64",
            "selected_record": "0x2000d00",
        })
        second = report["callbacks"]["second_fade"]
        self.assertEqual(second["count"], 1)
        self.assertEqual(second["entry"], {
            "r0": "0x2000e00",
            "r1": "0x1000120",
            "r2": "0x0",
            "r3": "0x1",
            "r4": "0x2000d00",
            "lr": "0x210014",
            "s0_bits": "0x3e800000",
            "s1_bits": "0x3f19999a",
            "s2_bits": "0x3f19999a",
            "s3_bits": "0x0",
            "fpscr": "0x20000000",
        })
        self.assertEqual(second["return"]["s0_bits"], "0x3e800000")
        self.assertEqual(report["callbacks"]["first_fade"]["count"], 1)
        self.assertEqual(report["callback_stub_contract"]["instruction"], "bx lr")
        self.assertEqual(report["callback_stub_contract"]["memory_writes"], [])
        self.assertEqual([(row["pc"], row["address"]) for row in report["indexed_table_reads"]], [
            ("0x20ffb0", "0x200062c"),
            ("0x20ffb8", "0x2000b48"),
            ("0x20ffc4", "0x2000a28"),
            ("0x20ffc8", "0x2000b4c"),
            ("0x20ffcc", "0x2000c48"),
            ("0x20ffd0", "0x2000c3c"),
            ("0x20ffd8", "0x2000c64"),
        ])
        self.assertEqual(report["unexpected_reads"], [])
        self.assertEqual(report["read_count"], 65)
        self.assertEqual(report["write_count"], 16)
        self.assertEqual(report["final_state"], {
            "selected_record_0x38": 0.25,
            "selected_record_0x3c": 0.8999999761581421,
            "selected_record_0x58": 1,
            "childB_transition_byte": 1,
            "work_0x94": 1,
        })


if __name__ == "__main__":
    unittest.main()
