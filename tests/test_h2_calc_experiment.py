import unittest

from tools.h2_calc_experiment import (
    Scenario, arm_special_helper_arguments, compare, directed_scenarios, tbb_row_offset,
)


class H2CalcExperimentTests(unittest.TestCase):
    def test_proven_tbb_row_offsets_and_wrong_stride_control(self):
        self.assertEqual([tbb_row_offset(i) for i in range(3)], [0x16, 0xAC, 0x142])
        self.assertNotEqual(0x16 + 0x56, tbb_row_offset(1))

    def test_directed_states_and_logical_queries_are_present(self):
        cases = directed_scenarios(7, 0)
        states = {case.state for case in cases}
        self.assertTrue({0, 1, 2, 3, 4, 5, 0x80000000}.issubset(states))
        self.assertIn("state1-noop", {case.label for case in cases})
        self.assertIn("state1-decrement-at-zero", {case.label for case in cases})
        self.assertIn("state1-increment-at-ten", {case.label for case in cases})

    def test_special_handle_cases_cover_s32_boundaries_and_arm_wrapping(self):
        cases = {case.label: case for case in directed_scenarios(7, 0)}
        expected = {
            "state1-special-wrap-max-minus-min":
                (0x7FFFFFFF, -(1 << 31), (0xFFFFFFF6, 10, 0xFFFFFFFB), 3),
            "state1-special-wrap-min-minus-max":
                (-(1 << 31), 0x7FFFFFFF, (10, 10, 5), 7),
            "state1-special-scale-positive-extreme":
                (0x7FFFFFFF, 0, (0xFFFFFFF6, 10, 0x7FFFFFFB), 10),
            "state1-special-scale-negative-extreme":
                (-(1 << 31), 0, (0, 10, 0x80000000), 0),
        }
        for label, (script_value, current_value, args, mapped) in expected.items():
            with self.subTest(label=label):
                case = cases[label]
                self.assertEqual((case.script_value, case.script_index),
                                 (script_value, current_value))
                self.assertEqual(arm_special_helper_arguments(script_value, current_value), args)
                self.assertGreaterEqual(case.bounded_value_result, 0)
                self.assertLessEqual(case.bounded_value_result, 10)
                self.assertEqual(case.bounded_value_result, mapped)

    def test_observation_comparator_detects_wrong_config_write(self):
        original = {"fault": None, "stopped": True, "preserved": (1,),
                    "expected_preserved": (1,), "return": 0, "pc": 2,
                    "work": b"work", "config": bytes.fromhex("3250503000000000"),
                    "trace": [("logical_query", 4, 0, 1)]}
        candidate = dict(original)
        self.assertIsNone(compare(original, candidate))
        candidate["config"] = bytes.fromhex("3250503100000000")
        self.assertEqual(compare(original, candidate), "config differs")


if __name__ == "__main__":
    unittest.main()
