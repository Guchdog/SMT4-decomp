from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.h3_title_caller_composition import run_experiment


class H3TitleCallerCompositionTest(unittest.TestCase):
    def test_state7_caller_composes_with_candidate_and_detects_wrong_state(self):
        with tempfile.TemporaryDirectory(prefix="h3-title-caller-") as temp:
            report = run_experiment(Path(temp) / "run")

        self.assertTrue(report["passed"])
        self.assertEqual(report["original"]["state"], 8)
        self.assertEqual(report["candidate"]["state"], 8)
        signature = lambda result: [(call["target"], call["args"][:2]) for call in result["calls"]]
        self.assertEqual(signature(report["original"]), signature(report["candidate"]))
        self.assertTrue(report["negative_control"]["detected"])
        self.assertEqual(report["negative_control_result"]["state"], 7)


if __name__ == "__main__":
    unittest.main()
