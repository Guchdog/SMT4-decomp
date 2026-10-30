import tempfile
import unittest
from pathlib import Path

from tools.h1_navigation_caller_experiment import (
    CONTINUE, GATE_EXIT, ROOT, run, verify_image,
)


class TestH1NavigationCallerExperiment(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image_path = ROOT / "extracted/exefs/code.bin"
        cls.image = cls.image_path.read_bytes()

    def test_pinned_image_and_original_windows(self):
        evidence = verify_image(self.image)
        self.assertEqual(evidence["sha256"], "1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558")
        self.assertEqual(evidence["size"], 3_633_152)
        self.assertEqual(evidence["windows"][0]["start"], "0x1e9d08")

    def test_wrong_revision_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            verify_image(self.image + b"changed")

    def test_compiled_caller_behavior_and_explicit_register_differences(self):
        with tempfile.TemporaryDirectory(prefix="h1-nav-caller-") as temp:
            report = run(self.image_path, Path(temp))
        self.assertTrue(report["passed"])
        self.assertEqual(report["evidence"]["compiled"], "passed")
        self.assertEqual(report["evidence"]["arm_differential"], "partial")
        self.assertEqual(report["evidence"]["caller"], "partial")
        self.assertEqual(report["evidence"]["runtime"], "not_run")
        self.assertEqual(len(report["readiness_cases"]), 3)
        self.assertTrue(all(case["passed_behavior"] for case in report["readiness_cases"]))
        self.assertEqual(len(report["directed_cases"]), 10)
        self.assertTrue(all(case["passed_behavior"] for case in report["directed_cases"]))
        self.assertEqual(report["exhaustive_valid_domain"]["case_count"], 256)
        self.assertTrue(report["exhaustive_valid_domain"]["passed"])
        self.assertTrue(all(case["passed_behavior"] for case in report["directed_cases"]))
        self.assertFalse(all(case["passed_full_state"] for case in report["directed_cases"]))
        self.assertTrue(all(case["original"]["stop"] in (CONTINUE, GATE_EXIT)
                            for case in report["readiness_cases"] + report["directed_cases"]))
        self.assertTrue(report["negative_control"]["rejected"])
        self.assertEqual(report["negative_control"]["original_result"], 3)
        self.assertNotEqual(report["negative_control"]["wrong_raw_signed_modulo_result"], 3)
        self.assertEqual(report["hook_contract"]["allowed_entry_hooks_only"],
                         ["0x289924", "0x25a2bc", "0x2b902c", "0x2b91c4"])


if __name__ == "__main__":
    unittest.main()
