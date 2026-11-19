import tempfile
import unittest
from pathlib import Path

from tools.h18_002e0dd0_experiment import FUNC, run

ROOT = Path(__file__).resolve().parents[1]

class TestH18002E0dd0Experiment(unittest.TestCase):
    def test_bounded_wrapper_and_real_caller_composition(self):
        with tempfile.TemporaryDirectory() as temp:
            result = run(ROOT / "extracted/exefs/code.bin", Path(temp), seed=7, samples=2)
        self.assertEqual(result["address"], hex(FUNC))
        self.assertTrue(result["passed"], result["first_failure"])
        self.assertEqual(result["direct"]["cases"], 27)
        self.assertEqual(len(result["callers"]), 3)
        self.assertTrue(all(item["passed"] for item in result["callers"]))
        self.assertEqual(
            {item["caller"]: item["expected_return"] for item in result["callers"]},
            {
                "ui_func_003bbdb8_ignored_result": 0x0043DDF2,
                "ui_func_003bbfb0_non5_returns_0": 0,
                "ui_func_003bbfb0_five_returns_11": 0x11,
            },
        )
        self.assertEqual(
            {item["caller"]: item["stop"] for item in result["callers"]},
            {
                "ui_func_003bbdb8_ignored_result": "0x3bbe18",
                "ui_func_003bbfb0_non5_returns_0": "0x1001000",
                "ui_func_003bbfb0_five_returns_11": "0x1001000",
            },
        )
        self.assertTrue(all(item["detected"] for item in result["negative_controls"]))

if __name__ == "__main__":
    unittest.main()
