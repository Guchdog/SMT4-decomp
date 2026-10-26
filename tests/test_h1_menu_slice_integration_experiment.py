"""Focused tests for the production H1 main-menu State-5 slice integration."""
from __future__ import annotations

import tempfile
from pathlib import Path
import unittest

from tools.h1_menu_slice_integration_experiment import (
    CALLBACK_SIZE,
    CODE_PATH,
    TBB_PATH,
    run_experiment,
)


class TestH1MenuSliceIntegrationExperiment(unittest.TestCase):
    @unittest.skipUnless(
        CODE_PATH.exists() and TBB_PATH.exists(),
        "Pinned code.bin and TitleTable.tbb are required for H1 slice integration test",
    )
    def test_production_h1_menu_slice_integration(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "run"
            report = run_experiment(out)
            self.assertTrue(report["passed"])
            self.assertEqual(report["slice_window"]["callback_total_bytes"], CALLBACK_SIZE)
            self.assertTrue(report["slice_window"]["prefix_bytes_identical"])
            self.assertTrue(report["slice_window"]["suffix_bytes_identical"])
            summary = report["navigation_matrix_summary"]
            self.assertEqual(summary["gate_false_passed"], 2)
            self.assertEqual(summary["matrix_passed"], 256)
            self.assertTrue(summary["pointer_mutation_passed"])
            self.assertTrue(summary["negative_control_detected"])
            self.assertEqual(len(report["transition_fade_help_cases"]), 4)
            for idx, case in enumerate(report["transition_fade_help_cases"]):
                self.assertEqual(case["selection"], idx)
                self.assertTrue(case["passed"])
                self.assertEqual(case["r1_color"], "0x323232ff")


if __name__ == "__main__":
    unittest.main()
