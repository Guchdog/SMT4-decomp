import tempfile
import unittest
from pathlib import Path

from tools.h2_pair_fill_experiment import CODE_DEFAULT, run_experiment


class H2PairFillExperimentTests(unittest.TestCase):
    def test_full_low_byte_domain_and_seeded_inputs_match(self):
        with tempfile.TemporaryDirectory(prefix="h2-pair-fill-") as temporary:
            report = run_experiment(CODE_DEFAULT, Path(temporary) / "seed-7", 7, 256)
        self.assertTrue(report["passed"], report)
        self.assertEqual(report["cases_passed"], 1280)
        self.assertIsNone(report["first_counterexample"])

    def test_wrong_one_word_control_is_detected(self):
        with tempfile.TemporaryDirectory(prefix="h2-pair-fill-control-") as temporary:
            report = run_experiment(CODE_DEFAULT, Path(temporary) / "seed-20261024",
                                    20261024, 256)
        self.assertTrue(report["negative_control"]["detected"], report)


if __name__ == "__main__":
    unittest.main()
