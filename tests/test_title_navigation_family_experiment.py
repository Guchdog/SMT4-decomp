import tempfile
import unittest
from pathlib import Path

from tools.title_navigation_family_experiment import (
    CORE_START, CORE_STOP, EXPECTED_SHA256, GATE_READY_STOP,
    GATE_RETURN_STOP, ROOT, run, verify_image,
)


class TestTitleNavigationFamilyExperiment(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image = (ROOT / "extracted/exefs/code.bin").read_bytes()

    def test_reference_image_and_windows_are_pinned(self):
        evidence = verify_image(self.image)
        self.assertEqual(evidence["sha256"], EXPECTED_SHA256)
        self.assertEqual([w["start"] for w in evidence["windows"]],
                         ["0x1e9d0c", "0x1e9d48"])

    def test_reference_hash_mismatch_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            verify_image(self.image + b"changed")

    def test_family_gate_trigger_wrap_cache_and_event_contract(self):
        with tempfile.TemporaryDirectory() as directory:
            report = run(ROOT / "extracted/exefs/code.bin", Path(directory))
        self.assertTrue(report["passed"])
        self.assertEqual(len(report["gate_tests"]), 3)
        self.assertEqual([g["result"]["pc"] for g in report["gate_tests"]],
                         [GATE_RETURN_STOP, GATE_RETURN_STOP, GATE_READY_STOP])
        self.assertTrue(report["exhaustive_valid_domain"]["passed"])
        self.assertEqual(report["exhaustive_valid_domain"]["case_count"], 256)
        self.assertEqual(len(report["cases"]), 11)
        self.assertTrue(all(case["passed"] for case in report["cases"]))
        by_name = {case["case"]: case for case in report["cases"]}
        self.assertEqual(by_name["previous-primary-wrap-0-to-3"]["original"]["trigger_calls"],
                         [5, 6, 0xF])
        self.assertEqual(by_name["previous-alias-wrap-0-to-3"]["original"]["trigger_calls"],
                         [5, 0xE, 6, 0xF])
        self.assertEqual(by_name["next-primary-wrap-3-to-0"]["original"]["trigger_calls"],
                         [5, 0xE, 6])
        self.assertEqual(by_name["next-alias-wrap-3-to-0"]["original"]["trigger_calls"],
                         [5, 0xE, 6, 0xF])
        self.assertEqual(by_name["both-directions-sequential-net-zero"]["original"]["trigger_calls"],
                         [5, 6])
        self.assertIn("0x002B91C4", report["stub_contracts"]["event"])
        self.assertTrue(any(case["original"]["events"] for case in report["cases"]))
        self.assertEqual(CORE_START, 0x001E9D48)
        self.assertEqual(CORE_STOP, 0x001E9DE0)


if __name__ == "__main__":
    unittest.main()
