"""Focused checks for the exact production-source H1 message bridge evidence."""
from __future__ import annotations

import json
import os
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
REPORT = Path(os.environ.get(
    "H1_TITLE_MESSAGE_BRIDGE_REPORT",
    ROOT / "build/agent-work/H1-semantic/h1-title-message-source-bridge/"
    "overnight-20261025-source-bridge-v1/run-04/report.json"))
EXPECTED = [
    (0, 0x46, 36, "Start a new game from the beginning."),
    (1, 0x9C, 39, "Load a saved game and continue playing."),
    (2, 0xF2, 25, "Configure audio settings."),
    (3, 0x148, 28, "Download additional content."),
]


class H1TitleMessageProductionBridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not REPORT.is_file():
            raise AssertionError(f"run the private production-source bridge first: {REPORT}")
        cls.report = json.loads(REPORT.read_text(encoding="utf-8"))

    def test_exact_production_tu_compiles_and_matches_pinned_helper(self):
        report = self.report
        self.assertTrue(report["passed"])
        self.assertEqual(report["case_count"], 10)
        self.assertTrue(all(case["passed"] for case in report["cases"]))
        self.assertEqual(report["evidence"]["compiled"], "passed")
        self.assertEqual(report["evidence"]["arm_differential"], "partial")
        self.assertEqual(report["evidence"]["runtime"], "not_run")
        for command in report["candidate"]["commands"]:
            self.assertEqual(command["exit_code"], 0, command["argv"])
        self.assertEqual(report["candidate"]["undefined_symbols"], [])
        asset_cases = [case for case in report["cases"] if case["selection"] is not None]
        self.assertEqual(len(asset_cases), 4)
        for case, (selection, file_offset, length, text) in zip(asset_cases, EXPECTED):
            self.assertEqual(case["selection"], selection)
            self.assertEqual(case["asset_file_offset"], file_offset)
            self.assertEqual(case["input_length"], length)
            self.assertEqual(case["text"], text)
            self.assertEqual(case["original"]["r0"], "0x1")
            self.assertEqual(case["candidate"]["r0"], "0x1")
            self.assertEqual(case["original"]["work_sha256"], case["candidate"]["work_sha256"])
            self.assertEqual(case["original"]["copy_calls"] and
                             case["original"]["copy_calls"][0]["args"][1],
                             hex(0x02000100 + file_offset))

    def test_null_reset_and_boundary_cases_are_in_the_projection(self):
        by_name = {case["name"]: case for case in self.report["cases"]}
        self.assertEqual(by_name["null-reset"]["original"]["r0"], "0xff")
        self.assertEqual(by_name["null-reset"]["candidate"]["r0"], "0xff")
        self.assertEqual(by_name["single-line-64-byte-boundary"]["input_length"], 65)
        self.assertEqual(by_name["two-lines-scan-end-terminator"]["input_length"], 128)
        self.assertTrue(by_name["two-lines-scan-end-terminator"]["passed"])
        self.assertTrue(by_name["high-bit-content"]["passed"])

    def test_invalid_manager_and_overlong_guards_are_separate_controls(self):
        controls = {item["name"]: item for item in self.report["controls"]}
        self.assertEqual(set(controls), {
            "overlong-first-line-guard", "overlong-second-line-guard",
            "unterminated-128-byte-guard", "null-work-manager-guard"})
        self.assertTrue(all(item["detected"] for item in controls.values()))
        self.assertTrue(all(item["candidate_return"] == "0x0" for item in controls.values()))
        self.assertTrue(controls["overlong-first-line-guard"]["workspace_unchanged"])
        self.assertTrue(controls["overlong-second-line-guard"]["workspace_unchanged"])
        self.assertTrue(controls["unterminated-128-byte-guard"]["workspace_unchanged"])
        self.assertTrue(controls["null-work-manager-guard"]["work_unchanged"])

    def test_bridge_is_h1_scoped_and_preserves_ledger_backed_bodies(self):
        checks = self.report["integration_checks"]
        self.assertTrue(checks["cmake_glob_includes_source"])
        self.assertTrue(checks["two_h1_calls_only"])
        self.assertTrue(checks["h1_calls_in_disabled_callback_draft"])
        self.assertTrue(checks["legacy_call_remains_disabled_non_h1_draft"])
        self.assertTrue(checks["one_api_declaration_definition"])
        self.assertTrue(checks["no_global_alias"])
        self.assertTrue(checks["original_helper_body_unchanged"])
        self.assertTrue(checks["shared_copy_body_unchanged"])
        self.assertTrue(checks["ledger_unchanged"])


if __name__ == "__main__":
    unittest.main()
