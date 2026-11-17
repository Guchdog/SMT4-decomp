import tempfile
import unittest
from pathlib import Path

from tools.h18_paired_store_integration import run, verify_source

ROOT = Path(__file__).resolve().parents[1]


class TestH18PairedStoreIntegration(unittest.TestCase):
    def test_production_declaration_and_body_keep_pointer_return(self):
        result = verify_source(ROOT)
        self.assertEqual(result["symbol"], "ui_func_00131414")
        self.assertEqual(result["stores"], [4, 8])
        self.assertTrue(result["independent_typed_stores"])
        self.assertEqual(result["return_offset"], 4)
        self.assertEqual(result["caller_declaration_return"], "u8*")

    def test_production_object_leaf_and_real_caller_window(self):
        with tempfile.TemporaryDirectory() as temp:
            report = run(ROOT / "extracted/exefs/code.bin", Path(temp), seed=7, samples=8)
        self.assertTrue(report["passed"])
        self.assertEqual(report["function"]["candidate_bytes"], 12)
        self.assertTrue(report["function"]["passed"])
        self.assertTrue(report["caller_window"]["passed"])
        self.assertEqual(report["caller_window"]["stop"], "0x121d24")
        self.assertTrue(all(control["detected"] for control in report["negative_controls"]))


if __name__ == "__main__":
    unittest.main()
