"""Keep Azahar execution-breakpoint tables aligned with patch manifests."""
import importlib.util
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
MONITOR_PATH = ROOT / "experiments/semantic_equivalence/azahar_hit_flag.py"
SPEC = importlib.util.spec_from_file_location("azahar_hit_flag", MONITOR_PATH)
MONITOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MONITOR)


def report_breakpoints(report_path):
    report = json.loads(report_path.read_text(encoding="utf-8"))
    names = {int(row["address"], 16): row["name"] for row in report["functions"]}
    return {
        int(patch["replacement"], 16): (
            int(patch["entry"], 16), names[int(patch["entry"], 16)])
        for patch in report["patches"]
    }


class TestAzaharHitFlag(unittest.TestCase):
    def test_default_preserves_historical_batch_2_monitor(self):
        self.assertEqual(MONITOR.parse_args([]).batch, "2")
        self.assertEqual(MONITOR.BREAKPOINTS, MONITOR.BATCH_BREAKPOINTS[2])
        self.assertEqual(len(MONITOR.BREAKPOINTS), 10)

    def test_batch_4_can_be_selected_without_changing_default(self):
        self.assertEqual(MONITOR.parse_args(["--batch", "4"]).batch, "4")
        self.assertEqual(MONITOR.parse_args(["--batch", "4", "--pid", "0x11"]).pid,
                         "0x11")
        self.assertEqual(len(MONITOR.BATCH_BREAKPOINTS[4]), 14)

    def test_batch_2_table_matches_report_patch_manifest(self):
        path = ROOT / "build/semantic-equivalence/batch-002-callers/seed-20261024/report.json"
        if not path.is_file():
            self.skipTest("batch-2 ignored report is not present in this checkout")
        self.assertTrue(json.loads(path.read_text(encoding="utf-8"))["passed"])
        self.assertEqual(MONITOR.BATCH_BREAKPOINTS[2], report_breakpoints(path))

    def test_batch_4_table_matches_report_patch_manifest(self):
        path = ROOT / "build/semantic-equivalence/batch-004-copy/seed-20261024/report.json"
        if not path.is_file():
            self.skipTest("batch-4 ignored report is not present in this checkout")
        self.assertTrue(json.loads(path.read_text(encoding="utf-8"))["passed"])
        self.assertEqual(MONITOR.BATCH_BREAKPOINTS[4], report_breakpoints(path))


if __name__ == "__main__":
    unittest.main()
