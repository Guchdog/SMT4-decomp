import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from tools.h1_type1_callback_experiment import ROOT, run_experiment


class TestH1Type1CallbackExperiment(unittest.TestCase):
    def test_pinned_arm_candidate_domain_and_mutation_controls(self):
        base = ROOT / "build/semantic-equivalence/real-assets/exefs/code.bin"
        source = ROOT / "experiments/semantic_equivalence/h1_type1_callback_candidate.cpp"
        with TemporaryDirectory(prefix="h1-type1-callback-") as output:
            report = run_experiment(base, source, Path(output))
        self.assertIn(report["outcome"], (
            "candidate_cases_passed", "passed_with_exceptional_domain_limit"))
        self.assertEqual(report["reference_sha256"],
                         "1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558")
        cases = {row["label"]: row for row in report["cases"]}
        for label in ("zero_interval", "equal_sample", "below_start", "inside_positive",
                      "at_upper", "above_upper", "negative_interval",
                      "negative_interval_below", "rounding_near_half", "qnan_sample"):
            self.assertEqual(cases[label]["mismatches"], [], label)
        self.assertTrue(cases["positive_infinity_sample"]["same_fault_domain_limit"])
        self.assertEqual(cases["positive_infinity_sample"]["mismatches"], [])
        self.assertTrue(report["negative_controls"]["ordered_nan_branch"]["mismatches"])
        self.assertTrue(report["negative_controls"]["skip_integral_helper"]["mismatches"])


if __name__ == "__main__":
    unittest.main()
