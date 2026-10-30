"""Focused assertions for the bounded H1 title/message differential."""
from __future__ import annotations

import json
import os
from pathlib import Path
import struct
import unittest

ROOT = Path(__file__).resolve().parents[1]
REPORT = Path(os.environ.get(
    "H1_TITLE_MESSAGE_REPORT",
    ROOT / "build/agent-work/H1-semantic/h1-title-message-real-asset-validation/"
    "overnight-20261025-title-message-real-asset-v1/run-02/report.json"))


class TitleMessageExperimentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not REPORT.is_file():
            raise AssertionError(f"run the private experiment first: {REPORT}")
        cls.report = json.loads(REPORT.read_text(encoding="utf-8"))
        cls.helper = {case["name"]: case for case in cls.report["helper_cases"]}

    def test_pinned_and_linked_domains_match(self):
        report = self.report
        self.assertTrue(report["passed"])
        self.assertEqual(report["first_mismatch"], None)
        self.assertEqual(report["helper_case_count"], 13)
        self.assertEqual(report["synthetic_helper_case_count"], 9)
        self.assertEqual(report["real_asset_case_count"], 4)
        self.assertEqual(report["copy_case_count"], 176)
        self.assertTrue(all(c["passed"] for c in report["helper_cases"] + report["copy_cases"]))
        self.assertEqual(report["candidate"]["undefined_symbols"], [])
        self.assertEqual(report["reference_image_sha256"],
                         "1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558")
        self.assertGreater(report["optimized_copy_path_coverage"]["direct_matrix_cases_entering_0x002BCF58"], 0)
        self.assertGreater(report["optimized_copy_path_coverage"]["helper_copy_calls_entering_0x002BCF58"], 0)

    def test_null_reset_and_nonnull_work_effects(self):
        null = self.helper["null color reset"]
        w = bytes.fromhex(null["original_work_hex"])
        self.assertEqual(int(null["original"]["r0"], 16), 0xFF)
        self.assertEqual(struct.unpack_from("<I", w, 0x4CC)[0], 0x323232FF)
        self.assertEqual(struct.unpack_from("<I", w, 0x550)[0], 0)
        self.assertEqual(w[0x554], 0xFF)
        self.assertEqual(w[0x4CB], 0)
        self.assertEqual(w[0x55C], 0xA7)

        empty = self.helper["empty nonnull string"]
        ew = bytes.fromhex(empty["original_work_hex"])
        self.assertEqual(int(empty["original"]["r0"], 16), 1)
        self.assertEqual(struct.unpack_from("<I", ew, 0x4CC)[0], 0x80402010)
        self.assertEqual(ew[0x4CB], 1)
        self.assertEqual(ew[0x55C], 0)
        self.assertEqual(ew[0x4D0:0x550], bytes(0x80))

    def test_line_and_scan_boundaries_stay_inside_declared_domain(self):
        max_one = bytes.fromhex(self.helper["one line max nominal slot length"]["original_work_hex"])
        self.assertEqual(max_one[0x4D0:0x510], b"A" * 64)
        self.assertEqual(max_one[0x510:0x550], bytes(0x40))

        edge = bytes.fromhex(self.helper["two bounded lines with NUL at scan index 127"]["original_work_hex"])
        self.assertEqual(edge[0x4D0:0x510], b"A" * 64)
        self.assertEqual(edge[0x510:0x54E], b"B" * 62)
        self.assertEqual(edge[0x54E:0x550], bytes(2))

        scan = self.helper["128 readable bytes without terminator stops without partial copy"]
        sw = bytes.fromhex(scan["original_work_hex"])
        self.assertEqual(int(scan["original"]["r0"], 16), 1)
        self.assertEqual(sw[0x4D0:0x550], bytes(0x80))
        self.assertTrue(any("128 readable" in x for x in self.report["limitations"]))

    def test_copy_matrix_and_three_mutation_controls(self):
        self.assertEqual({c["dest_alignment"] for c in self.report["copy_cases"]}, {0, 1, 2, 3})
        self.assertEqual({c["source_alignment"] for c in self.report["copy_cases"]}, {0, 1, 2, 3})
        self.assertEqual({c["length"] for c in self.report["copy_cases"]},
                         {0, 1, 2, 3, 4, 7, 8, 9, 31, 32, 33})
        controls = {control["name"]: control for control in self.report["negative_controls"]}
        self.assertEqual(set(controls), {"wrong_null_mode_return", "omitted_color_store", "corrupt_forward_copy_bytes"})
        self.assertTrue(all(control["detected"] for control in controls.values()))
        self.assertIn("r0 differs", controls["wrong_null_mode_return"]["case"]["errors"])
        self.assertTrue(controls["omitted_color_store"]["case"]["first_memory_mismatch"])
        self.assertTrue(controls["corrupt_forward_copy_bytes"]["case"]["first_memory_mismatch"])

    def test_four_real_h1_help_rows_use_pinned_payload_formula_and_fit(self):
        asset = self.report["real_asset"]
        self.assertEqual(asset["size"], 880)
        self.assertEqual(asset["sha256"],
                         "edd6bc1de5388e5689f797861ae6947c7c339f9b6bdb63d6c35951d72020fa41")
        self.assertEqual(asset["table0"]["offset"], 0x20)
        self.assertEqual(asset["payload_file_offset"], 0x30)
        self.assertEqual(asset["h1_row_stride"], 0x56)
        self.assertEqual(asset["h1_string_field_offset"], 0x16)
        expected_offsets = [0x46, 0x9C, 0xF2, 0x148]
        expected_payload_offsets = [0x16, 0x6C, 0xC2, 0x118]
        expected_text = [b"Start a new game from the beginning.",
                         b"Load a saved game and continue playing.",
                         b"Configure audio settings.",
                         b"Download additional content."]
        cases = [case for case in self.report["helper_cases"] if "asset_row_index" in case]
        self.assertEqual([case["asset_row_index"] for case in cases], [0, 1, 2, 3])
        for index, case in enumerate(cases):
            row = asset["rows"][index]
            self.assertEqual(row["string_file_offset"], expected_offsets[index])
            self.assertEqual(row["string_payload_offset"], expected_payload_offsets[index])
            self.assertEqual(row["string_ascii"].encode("ascii"), expected_text[index])
            self.assertEqual(case["asset_string_file_offset"], expected_offsets[index])
            self.assertEqual(case["asset_string_payload_offset"], expected_payload_offsets[index])
            self.assertEqual(case["asset_string_runtime_pointer"],
                             0x02000000 + 0x10000 + expected_offsets[index])
            self.assertEqual(case["asset_line_lengths"], [len(expected_text[index])])
            self.assertLessEqual(max(case["asset_line_lengths"]), 64)
            work = bytes.fromhex(case["original_work_hex"])
            self.assertEqual(work[0x4D0:0x4D0 + len(expected_text[index])], expected_text[index])
            self.assertEqual(work[0x4D0 + len(expected_text[index]):0x550],
                             bytes(0x80 - len(expected_text[index])))

    def test_evidence_and_runtime_limits(self):
        self.assertEqual(self.report["evidence"]["compiled"], "passed")
        self.assertEqual(self.report["evidence"]["arm_differential"], "partial_bounded_synthetic")
        self.assertEqual(self.report["evidence"]["caller"], "not_run")
        self.assertEqual(self.report["evidence"]["runtime"], "not_run")
        self.assertTrue(any("TBB" in x for x in self.report["limitations"]))
        self.assertTrue(any("overlap" in x for x in self.report["limitations"]))


if __name__ == "__main__":
    unittest.main()
