import unittest

from tools.h2_logical_mode0_query_experiment import (
    COUNTER_VALUES,
    FLAGS_VALUES,
    INVALID_IDS,
    SELECTORS,
    THRESHOLDS,
    VALID_IDS,
    expected,
    helper_arguments_expected,
    helper_calls_expected,
)


class H2LogicalMode0QueryTests(unittest.TestCase):
    def test_all_valid_ids_thresholds_selectors_flags_and_counter_boundaries(self):
        self.assertEqual(VALID_IDS, tuple(range(31)))
        self.assertEqual(len(VALID_IDS) * len(FLAGS_VALUES) * len(THRESHOLDS) *
                         len(SELECTORS) * len(COUNTER_VALUES), 140864)

    def test_counter_one_is_initial_pulse_and_threshold_repeat_is_divisor_based(self):
        self.assertEqual(expected(4, 0, 1, 7, 2), 1)
        self.assertEqual(expected(4, 0, 7, 7, 2), 0)
        self.assertEqual(expected(4, 0, 9, 7, 2), 1)
        self.assertEqual(expected(4, 0, 10, 7, 2), 0)

    def test_flag_and_invalid_id_return_zero(self):
        self.assertEqual(expected(4, 1, 1, 7, 2), 0)
        self.assertEqual(expected(31, 0, 1, 7, 2), 0)
        self.assertTrue(all(value >= 31 for value in INVALID_IDS))

    def test_selector_zero_is_excluded_from_the_defined_test_domain(self):
        self.assertNotIn(0, SELECTORS)
        self.assertTrue(all(value > 0 for value in SELECTORS))

    def test_division_dependency_is_called_only_for_threshold_fallback(self):
        self.assertTrue(helper_calls_expected(4, 0, 9, 7))
        self.assertFalse(helper_calls_expected(4, 0, 1, 7))
        self.assertFalse(helper_calls_expected(4, 1, 9, 7))
        self.assertFalse(helper_calls_expected(31, 0, 9, 7))
        self.assertEqual(helper_arguments_expected(4, 0, 9, 7, 2), [(2, 2)])
        self.assertEqual(helper_arguments_expected(4, 0, 1, 7, 2), [])


if __name__ == "__main__":
    unittest.main()
