import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "experiments/semantic_equivalence/h1_preview_helper_candidate.cpp"


class PreviewHelperCandidateTests(unittest.TestCase):
    def test_candidate_keeps_external_dependencies_explicit(self):
        source = SOURCE.read_text(encoding="utf-8")
        for symbol in (
            "camp_func_002bdac0", "ui_func_002c615c", "ui_func_002b1fc0",
            "ui_func_002b1dfc", "ui_func_002b1c8c",
        ):
            self.assertIn('extern "C"', source)
            self.assertIn(symbol, source)
        self.assertIn("row_mode == 0 && object[0x84] != 0", source)
        self.assertIn("next_word", source)
        self.assertIn("next[4]", source)
        self.assertIn("object[0x86] = 1", source)

    def test_private_arm_report_includes_negative_control_and_boundaries(self):
        report_path = (ROOT / "build/agent-work/H1-semantic/h1-preview-helper-branch-coverage/"
                       "overnight-20261025-preview-helper-coverage/run-01/report.json")
        self.assertTrue(report_path.is_file(), "run h1_preview_helper_experiment.py first")
        report = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertEqual(report["task_id"], "h1-preview-helper-candidate")
        self.assertEqual(report["case_count"], 21)
        names = {item["name"] for item in report["cases"]}
        self.assertIn("null early return", names)
        self.assertIn("both negative early return", names)
        self.assertIn("interpolation row invokes two interpolators", names)
        self.assertIn("first gate zero with second gate negative continues", names)
        self.assertIn("signed minimum pair early return", names)
        self.assertIn("signed maximum then minimum continues without second gate", names)
        self.assertIn("row mode zero direction one endpoint", names)
        self.assertIn("row mode nonzero direction one endpoint", names)
        self.assertIn("direction one interpolation uses reversed deltas", names)
        self.assertIn("next sequence -3 marker sets complete", names)
        self.assertTrue(all(item["passed"] for item in report["cases"]))
        self.assertTrue(report["negative_controls"][0]["detected"])
        self.assertIn("synthetic", " ".join(report["limitations"]).lower())


if __name__ == "__main__":
    unittest.main()
