from __future__ import annotations

import os
from pathlib import Path
import time
import unittest

from tools.h2_secondary_experiment import make_cases, run_experiment


class H2SecondaryExperimentTests(unittest.TestCase):
    def test_directed_case_matrix(self):
        cases = {case["label"]: case for case in make_cases()}
        self.assertEqual(cases["counter-a-negative"]["counter_a"], -1)
        self.assertEqual(cases["counter-b-four"]["counter_b"], 4)
        self.assertFalse(cases["script-null"]["script"])
        self.assertFalse(cases["first-null"]["first"])
        self.assertFalse(cases["second-null"]["second"])
        self.assertFalse(cases["task-active-false"]["active"])
        self.assertTrue(cases["task-active-true"]["active"])
        self.assertEqual(
            [cases[f"manager-boundary-{n}"]["manager_halfword"] for n in (9, 10, 11, 12)],
            [9, 10, 11, 12],
        )

    def test_compiled_callback_differential_and_negative_controls(self):
        output_value = os.environ.get("H2_SECONDARY_TEST_OUTPUT")
        if not output_value:
            checks_root = Path(
                "build/agent-work/H2-semantic/h2-secondary-candidate/run-001/checks"
            )
            checks_root.mkdir(parents=True, exist_ok=True)
            output_value = str(checks_root / f"unittest-{os.getpid()}-{time.time_ns()}")
        report = run_experiment(
            Path("extracted/exefs/code.bin"), Path(output_value), seed=20261025
        )
        self.assertTrue(report["passed"], report["first_counterexample"])
        self.assertEqual(report["cases_compared"], report["cases_total"])
        self.assertTrue(all(item["detected"] for item in report["negative_controls"]))


if __name__ == "__main__":
    unittest.main()
