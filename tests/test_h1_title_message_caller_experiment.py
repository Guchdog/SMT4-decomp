"""Focused assertions for the state-5 caller/helper composition report."""
from __future__ import annotations

import json
import os
from pathlib import Path
import struct
import unittest

ROOT = Path(__file__).resolve().parents[1]
REPORT = Path(os.environ.get(
    "H1_TITLE_MESSAGE_CALLER_REPORT",
    ROOT / "build/agent-work/H1-semantic/h1-title-message-caller-composition/"
    "overnight-20261025-caller-compose-v1/run-05/report.json"))
EXPECTED = [
    (0x02000146, "Start a new game from the beginning."),
    (0x0200019C, "Load a saved game and continue playing."),
    (0x020001F2, "Configure audio settings."),
    (0x02000248, "Download additional content."),
]


class TitleMessageCallerCompositionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not REPORT.is_file():
            raise AssertionError(f"run the private composition experiment first: {REPORT}")
        cls.report = json.loads(REPORT.read_text(encoding="utf-8"))

    def test_four_real_rows_execute_original_caller_and_linked_candidate(self):
        report = self.report
        self.assertTrue(report["passed"])
        self.assertIsNone(report["first_mismatch"])
        self.assertEqual(report["case_count"], 4)
        self.assertTrue(all(case["passed"] for case in report["cases"]))
        self.assertEqual(report["asset"]["sha256"],
                         "edd6bc1de5388e5689f797861ae6947c7c339f9b6bdb63d6c35951d72020fa41")
        self.assertEqual(report["asset"]["payload_file_offset"], 0x30)
        for selection, case in enumerate(report["cases"]):
            pointer, text = EXPECTED[selection]
            self.assertEqual(case["selection"], selection)
            self.assertEqual(case["text"], text)
            self.assertEqual(case["expected_row_pointer"], hex(pointer))
            self.assertEqual(case["original"]["pre_call"]["r0"], hex(pointer))
            self.assertEqual(case["candidate"]["pre_call"]["r0"], hex(pointer))
            self.assertEqual(case["original"]["pre_call"]["r1"], "0x323232ff")
            self.assertEqual(case["candidate"]["pre_call"]["r1"], "0x323232ff")
            self.assertEqual(case["original"]["helper_entry"]["r0"], hex(pointer))
            self.assertEqual(case["candidate"]["helper_entry"]["r0"], hex(pointer))
            for side in ("original", "candidate"):
                observed = case[side]
                self.assertEqual(observed["pc"], "0x1ea160")
                self.assertEqual(observed["registers"]["r0"], "0x1")
                self.assertEqual(observed["registers"]["sp"], "0x8001000")
                self.assertTrue(observed["asset_unchanged"])
            self.assertEqual(case["original"]["data_sha256"], case["candidate"]["data_sha256"])
            self.assertEqual(case["original"]["help_work_hex"], case["candidate"]["help_work_hex"])
            work = bytes.fromhex(case["original"]["help_work_hex"])
            self.assertEqual(work[0x4D0:0x4D0 + len(text)], text.encode("ascii"))
            self.assertEqual(struct.unpack_from("<I", work, 0x4CC)[0], 0x323232FF)
            self.assertEqual(work[0x4CB], 1)
            self.assertEqual(work[0x554], 0xFF)
            self.assertEqual(work[0x55C], 0)

    def test_private_patch_changes_only_the_helper_bl(self):
        caller = self.report["caller_window"]
        self.assertEqual(caller["start"], "0x1ea12c")
        self.assertEqual(caller["call_pc"], "0x1ea15c")
        self.assertEqual(caller["stop_after_helper_return"], "0x1ea160")
        self.assertEqual(caller["pinned_call_word"], "ead302eb")
        self.assertEqual(caller["candidate_bl_word"], "b35738eb")
        self.assertEqual(caller["candidate_image_patch_width"], 4)
        self.assertEqual(caller["candidate_image_diff_bytes"], 3)
        self.assertEqual(caller["candidate_image_changed_offsets"],
                         [hex(0x1EA15C - 0x00100000 + i) for i in range(3)])
        self.assertEqual(caller["candidate_routes_to"], "0x1000030")
        self.assertEqual(caller["original_routes_to"], "0x29f10c")
        self.assertEqual(self.report["candidate"]["undefined_symbols"], [])

    def test_wrong_row_control_fails_entry_pointer_and_output_projection(self):
        control = self.report["wrong_row_control"]
        self.assertTrue(control["detected"])
        self.assertEqual(control["pre_call_pointer"], "0x200019c")
        self.assertEqual(control["expected_selection1_pointer"], "0x200019c")
        self.assertEqual(control["wrong_helper_entry_pointer"], "0x2000146")
        self.assertEqual(control["expected_selection0_pointer"], "0x2000146")
        self.assertTrue(control["candidate_entry_pointer_rejected"])
        self.assertTrue(control["final_help_work_differs_from_original"])
        self.assertIsNotNone(control["first_memory_mismatch"])

    def test_projection_and_runtime_limits_are_explicit(self):
        self.assertEqual(self.report["evidence"]["compiled"], "passed")
        self.assertEqual(self.report["evidence"]["arm_differential"],
                         "partial_real_asset_caller_window")
        self.assertEqual(self.report["evidence"]["caller"], "partial_state5_window_only")
        self.assertEqual(self.report["evidence"]["runtime"], "not_run")
        self.assertTrue(any("synthetic active-state caller frame" in item
                            for item in self.report["limitations"]))
        self.assertTrue(any("production integration/placement" in item
                            for item in self.report["limitations"]))


if __name__ == "__main__":
    unittest.main()
