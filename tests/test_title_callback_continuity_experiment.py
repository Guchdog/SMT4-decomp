import tempfile
import unittest
from pathlib import Path

from tools.title_callback_continuity_experiment import (
    EXPECTED_SHA256, ROOT, TOUCH_STOP, run, verify_image,
)


class TestTitleCallbackContinuityExperiment(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image = (ROOT / "extracted/exefs/code.bin").read_bytes()

    def test_reference_image_pins_all_three_contiguous_windows(self):
        evidence = verify_image(self.image)
        self.assertEqual(evidence["sha256"], EXPECTED_SHA256)
        self.assertEqual([w["start"] for w in evidence["windows"]],
                         ["0x1e9d48", "0x1e9de0", "0x1e9e4c"])
        self.assertEqual([w["stop"] for w in evidence["windows"]],
                         ["0x1e9de0", "0x1e9e4c", "0x1e9eb8"])
        self.assertEqual(TOUCH_STOP, 0x001E9EB8)

    def test_reference_hash_mismatch_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            verify_image(self.image + b"changed")

    def test_continuous_arm_and_hybrid_reducers_share_work_and_fp_state(self):
        with tempfile.TemporaryDirectory() as directory:
            report = run(ROOT / "extracted/exefs/code.bin", Path(directory))
        self.assertTrue(report["passed"])
        self.assertEqual(len(report["cases"]), 4)
        for case in report["cases"]:
            self.assertTrue(case["passed"], case["case"])
            original = case["original_continuous_arm"]
            self.assertEqual([stage["pc"] for stage in original["stages"]],
                             [0x001E9DE0, 0x001E9E4C, TOUCH_STOP])
            self.assertEqual(original["stages"][-1]["stopped"], True)
        for case in report["cases"][:3]:
            hybrid = case["hybrid_reducers_with_arm_vfp"]
            self.assertIsNotNone(hybrid)
            self.assertEqual(hybrid["anim_value_bits"],
                             case["original_continuous_arm"]["anim_value_bits"])
            self.assertEqual(hybrid["fp"], case["original_continuous_arm"]["fp"])
            self.assertEqual(hybrid["touch_calls"], [])
            original = case["original_continuous_arm"]
            self.assertEqual([entry["global_call"] for entry in original["touch_calls"]],
                             list(range(1, 13)))
            self.assertEqual(original["touch_call_counts"],
                             {"0x174": 3, "0x176": 3, "0x178": 3, "0x17a": 3})
            expected_trigger_order = {
                "stable-neutral-and-state6": [5, 14, 6, 15],
                "navigation-event-and-vfp-clamp": [5, 14, 6],
                "wrap-and-touch-confirm": [5, 6, 15],
            }
            self.assertEqual([entry["id"] for entry in original["trigger_calls"]],
                             expected_trigger_order[case["case"]])
        event_case = report["cases"][1]
        event_args = event_case["original_continuous_arm"]["event_calls"][0]["args_r0_r3"]
        self.assertEqual(event_args[0], 0x0100016C)
        self.assertEqual(len(event_args), 4)
        self.assertEqual(event_args[1], 2)
        variable = report["cases"][3]["original_continuous_arm"]["touch_calls"]
        self.assertEqual(len(variable), 12)
        self.assertEqual([item["global_call"] for item in variable], list(range(1, 13)))
        self.assertEqual(variable[:4], [
            {"handle": 0x174, "ordinal_for_handle": 1, "global_call": 1, "response": 3},
            {"handle": 0x174, "ordinal_for_handle": 2, "global_call": 2, "response": 0},
            {"handle": 0x176, "ordinal_for_handle": 1, "global_call": 3, "response": 0},
            {"handle": 0x176, "ordinal_for_handle": 2, "global_call": 4, "response": 3},
        ])
        self.assertIn("only on original ARM", report["limits"][1])


if __name__ == "__main__":
    unittest.main()
