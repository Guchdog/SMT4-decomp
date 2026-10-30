import unittest

from tools.h2_logical_query_caller_composition import (
    absolute_gates,
    compare_runs,
    logical_counter_seed,
    scenarios,
)
from tools.h2_calc_experiment import Scenario


class H2LogicalQueryCallerCompositionTests(unittest.TestCase):
    def test_h2_primary_and_fallback_cases_are_included(self):
        labels = {scenario.label for scenario in scenarios()}
        self.assertIn("mode0-fallback-D", labels)
        self.assertIn("mode0-fallback-C", labels)
        self.assertIn("mode0-primary-trigger", labels)
        self.assertIn("mode1-H2-ID9", labels)

    def test_logical_results_seed_one_pulse_counters(self):
        case = Scenario("seed", 1, logical={(4, 0): 1, (0xD, 0): 0, (9, 1): 1})
        counters = logical_counter_seed(case)
        self.assertEqual(counters[4], 1)
        self.assertEqual(counters[0xD], 0)
        self.assertEqual(counters[9], 1)
        self.assertEqual(counters[10], 0)

    def test_conflicting_mode_results_for_shared_id_are_rejected(self):
        case = Scenario("conflict", 1, logical={(4, 0): 0, (4, 1): 1})
        with self.assertRaisesRegex(ValueError, "incompatible modes"):
            logical_counter_seed(case)

    def test_absolute_gates_require_clean_stop_and_expected_preservation(self):
        clean = {"fault": None, "stopped": True, "preserved": (1, 2),
                 "expected_preserved": (1, 2)}
        self.assertEqual(absolute_gates(clean), {
            "no_fault": True,
            "reached_return_sentinel": True,
            "preserved_abi_state": True,
        })

    def test_matching_faults_do_not_count_as_a_pass(self):
        faulted = {"fault": "invalid instruction", "stopped": False,
                   "preserved": (1, 2), "expected_preserved": (1, 2)}
        self.assertIn("original fault", compare_runs(faulted, faulted))

    def test_matching_abi_corruption_does_not_count_as_a_pass(self):
        corrupted = {"fault": None, "stopped": True, "preserved": (1, 0),
                     "expected_preserved": (1, 2)}
        self.assertIn("violates callee-saved", compare_runs(corrupted, corrupted))


if __name__ == "__main__":
    unittest.main()
