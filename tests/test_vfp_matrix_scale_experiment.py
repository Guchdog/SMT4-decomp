from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from tools.vfp_matrix_scale_experiment import EXPECTED, FUNCTIONS, SPECIAL, run


ROOT = Path(__file__).resolve().parents[1]


class VfpMatrixScaleExperimentTests(unittest.TestCase):
    def test_pinned_matrix_scale_instruction_sequence(self):
        self.assertEqual(len(EXPECTED), 13)
        self.assertEqual(FUNCTIONS, {
            0x0023D368: ("candidate_0023d368", 52),
            0x0023E55C: ("candidate_0023e55c", 52),
        })
        self.assertEqual(len(SPECIAL), 16)

    def test_two_seed_differential_runs(self):
        with tempfile.TemporaryDirectory(prefix="vfp-matrix-scale-") as temporary:
            for seed in (20261024, 7):
                output = Path(temporary) / f"seed-{seed}"
                report = run(ROOT / "extracted/exefs/code.bin", output, seed)
                self.assertTrue(report["passed"], json.dumps(report, indent=2))
                self.assertFalse(report["fast_math"])
                self.assertEqual(report["seed"], seed)
                self.assertEqual(report["special_fpscr_cases"], 256)
                self.assertEqual(report["alias_cases"], 6)
                self.assertEqual(report["caller_windows"], [])
                self.assertEqual(len(report["functions"]), 2)
                for function in report["functions"]:
                    self.assertTrue(function["passed"], function)
                    self.assertEqual(function["cases"], 358)
                    self.assertEqual(function["original_bytes"], 52)
                    self.assertGreater(function["candidate_bytes"], 0)
                    self.assertEqual(function["callee_saved_vfp_registers"], "s16-s31 (d8-d15)")
                    footprint = function["separate_buffer_access_footprint"]
                    self.assertEqual(footprint["reference_read_bytes"], 60)
                    self.assertEqual(footprint["candidate_read_bytes"], 60)
                    self.assertEqual(footprint["reference_write_bytes"], 48)
                    self.assertEqual(footprint["candidate_write_bytes"], 48)
                    self.assertTrue(footprint["read_sets_exact"])
                    self.assertTrue(footprint["write_sets_exact"])
                self.assertTrue(all(control["detected"] for control in report["negative_controls"]))
                self.assertEqual(json.loads((output / "report.json").read_text(encoding="utf-8")), report)


if __name__ == "__main__":
    unittest.main()
