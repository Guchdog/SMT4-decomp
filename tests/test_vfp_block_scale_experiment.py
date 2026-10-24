from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from tools.vfp_block_scale_experiment import (
    EXPECTED,
    FUNCTIONS,
    SPECIAL,
    run,
)


ROOT = Path(__file__).resolve().parents[1]


class VfpBlockScaleExperimentTests(unittest.TestCase):
    def test_reference_instruction_sequence_is_16_vfp_instructions(self):
        self.assertEqual(len(EXPECTED), 16)
        self.assertEqual(FUNCTIONS, {
            0x0015F6D4: ("candidate_0015f6d4", 64),
            0x00256ED8: ("candidate_00256ed8", 64),
        })
        self.assertEqual(len(SPECIAL), 16)

    def test_two_seed_differential_runs(self):
        with tempfile.TemporaryDirectory(prefix="vfp-block-scale-") as temp:
            for seed in (20261024, 7):
                output = Path(temp) / f"seed-{seed}"
                report = run(ROOT / "extracted/exefs/code.bin", output, seed)
                self.assertTrue(report["passed"], json.dumps(report, indent=2))
                self.assertFalse(report["fast_math"])
                self.assertEqual(report["seed"], seed)
                self.assertEqual(report["edge_case_matrix"], 256)
                self.assertEqual(report["alias_cases"], 6)
                self.assertEqual(report["caller_windows"], [])
                self.assertEqual(len(report["functions"]), 2)
                for function in report["functions"]:
                    self.assertTrue(function["passed"], function)
                    self.assertEqual(function["cases"], 358)
                    self.assertEqual(function["original_bytes"], 64)
                    self.assertGreater(function["candidate_bytes"], 0)
                    self.assertFalse(function["full_s_register_exact"])
                    self.assertEqual(function["abi_preserved_vfp_registers"], "s16-s31 (d8-d15)")
                    self.assertTrue(all(
                        register < 16
                        for sample in function["s_register_differences_sample"]
                        for register in sample["registers"]
                    ))
                    footprint = function["separate_buffer_access_footprint"]
                    self.assertEqual(footprint["reference_read_bytes"], 60)
                    self.assertEqual(footprint["candidate_read_bytes"], 60)
                    self.assertEqual(footprint["reference_write_bytes"], 48)
                    self.assertEqual(footprint["candidate_write_bytes"], 48)
                    self.assertTrue(footprint["read_sets_exact"])
                    self.assertTrue(footprint["write_sets_exact"])
                self.assertTrue(all(x["detected"] for x in report["negative_controls"]))
                saved = json.loads((output / "report.json").read_text(encoding="utf-8"))
                self.assertEqual(saved, report)


if __name__ == "__main__":
    unittest.main()
