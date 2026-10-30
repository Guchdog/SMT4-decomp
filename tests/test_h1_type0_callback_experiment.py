from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
PACKET_OUTPUT = ROOT / "build/agent-work/H1-semantic/h1-type0-callback-semantic-correction/overnight-20261025-type0-callback-correction"


class H1Type0CallbackExperimentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.output = PACKET_OUTPUT / "test-run"
        cls.output.mkdir(parents=True, exist_ok=True)
        result = subprocess.run(
            [sys.executable, str(ROOT / "tools/h1_type0_callback_experiment.py"),
             "--output", str(cls.output)],
            cwd=ROOT, text=True, capture_output=True, check=False,
        )
        if result.returncode:
            raise AssertionError(f"runner failed ({result.returncode}): {result.stdout}\n{result.stderr}")
        cls.report = json.loads((cls.output / "report.json").read_text(encoding="utf-8"))

    def test_all_defined_contract_cases_match(self):
        self.assertTrue(self.report["passed"])
        self.assertEqual(len(self.report["cases"]), 17)
        self.assertTrue(all(case["matched"] for case in self.report["cases"]))

    def test_negative_control_is_rejected_for_unordered_cases(self):
        controls = self.report["negative_controls"]
        self.assertEqual(len(controls), 4)
        self.assertTrue(all(control["rejected"] for control in controls))
        self.assertTrue(all(control["same_s0"] for control in controls))
        self.assertTrue(all(control["fpscr_differs"] for control in controls))
        self.assertTrue(all(control["original_s0"] == control["wrong_s0"] and
                            control["original_fpscr"] != control["wrong_fpscr"]
                            for control in controls))

    def test_entry_and_abi_are_explicit(self):
        self.assertEqual(self.report["entry"], "0x15555c")
        self.assertEqual(self.report["predecessor_return"], "0x155558")
        self.assertIn("lower=s0, upper=s1, value=s2", self.report["abi"])


if __name__ == "__main__":
    unittest.main()
