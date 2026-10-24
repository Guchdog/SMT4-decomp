import unittest

from tools.title_transition_ready_path_experiment import (
    EXPECTED_HELP, ROOT, run,
)


class TestTitleTransitionReadyPathExperiment(unittest.TestCase):
    def test_continuous_original_arm_reaches_help_call_boundary(self):
        report = run(ROOT / "extracted/exefs/code.bin",
                     ROOT / "build/semantic-equivalence/real-assets/romfs/title/TitleTable.tbb")
        self.assertTrue(report["passed"])
        self.assertEqual([row["text"] for row in report["selections"]], list(EXPECTED_HELP))
        self.assertEqual(report["stop_before_call"], "0x1ea15c")
        self.assertEqual(report["presentation_callee_not_entered"], "0x29f10c")
        expected_calls = ["0x25a274", "0x2d569c", "0x2c0ec4", "0x2ac2f4", "0x2c0e9c"]
        expected_pointer_base = 0x02000146
        expected_reads = {
            0x02000808, 0x0200088C, 0x02000894, 0x02000C08,
            0x02000D34, 0x02000D58, 0x00493BD0,
            0x02000100, 0x02000104, 0x02000108, 0x0200010C, 0x02000120,
            0x001E9EC4, 0x002C0EDC, 0x002AC348, 0x002AC34C, 0x002C0EC0,
        }
        for row in report["selections"]:
            self.assertTrue(all(row["reached"].values()), row["selection"])
            calls = row["call_entries"]
            self.assertEqual([call["target"] for call in calls], expected_calls)
            self.assertEqual(int(calls[0]["r0_r3"][0], 16), 0x02000D00)
            self.assertEqual(int(calls[1]["r0_r3"][0], 16), 0x02000D00)
            self.assertEqual([int(value, 16) for value in calls[2]["r0_r3"][:2]],
                             [0x3A, 0])
            self.assertEqual([int(value, 16) for value in calls[3]["r0_r3"][:2]],
                             [0x02000100, 0])
            self.assertEqual(int(calls[4]["r0_r3"][0], 16), 0x02000120)
            self.assertEqual(row["pre_presentation_call_args"]["r1"], "0x323232ff")
            self.assertEqual(int(row["pre_presentation_call_args"]["r0"], 16),
                             expected_pointer_base + 0x56 * row["selection"])
            self.assertEqual({int(value, 16) for value in row["distinct_read_addresses"]},
                             expected_reads)
            self.assertEqual(row["read_count"], 20)
            self.assertEqual(row["writes"], [])
            self.assertEqual(row["setup"]["work_0x94"], 1)
            self.assertEqual(row["setup"]["child_0x34_signed"], 0)
            self.assertEqual(row["setup"]["child_0x58_signed"], 0)


if __name__ == "__main__":
    unittest.main()
