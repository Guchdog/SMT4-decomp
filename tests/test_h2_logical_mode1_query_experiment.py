import unittest

from tools.h2_logical_mode1_query_experiment import (
    COUNTER_VALUES,
    FLAG_VALUES,
    INVALID_IDS,
    VALID_IDS,
    compare,
    expected,
)


class H2LogicalMode1QueryTests(unittest.TestCase):
    def test_id_domain_and_matrix_cover_all_31_counters(self):
        self.assertEqual(VALID_IDS, tuple(range(31)))
        self.assertEqual(COUNTER_VALUES, (0, 1, 2, 0xFFFFFFFF))
        self.assertEqual(FLAG_VALUES, (0, 1, 2, 3))
        self.assertEqual(len(VALID_IDS) * len(COUNTER_VALUES) * len(FLAG_VALUES), 496)

    def test_invalid_domain_includes_unsigned_and_sign_boundary_values(self):
        self.assertEqual(INVALID_IDS, (31, 32, 0x7FFFFFFF, 0x80000000, 0xFFFFFFFF))

    def test_upper_bound_case_has_a_readable_adjacent_counter_sentinel(self):
        self.assertEqual(INVALID_IDS[0], 31)

    def test_query_returns_one_only_for_counter_one_with_availability_bit_clear(self):
        self.assertEqual(expected(9, 0, 1), 1)
        self.assertEqual(expected(0, 2, 1), 1)
        self.assertEqual(expected(9, 1, 1), 0)
        self.assertEqual(expected(9, 0, 2), 0)
        self.assertEqual(expected(31, 0, 1), 0)

    def test_comparator_detects_wrong_return_and_abi(self):
        state = {"fault": None, "return": 1, "pc": 0x1000, "sp": 0x8000,
                 "preserved": {"r4": True, "r11": True}}
        self.assertIsNone(compare(state, dict(state)))
        self.assertEqual(compare(state, dict(state, **{"return": 0})), "return differs")
        self.assertEqual(compare(state, dict(state, sp=0x7FFC)), "sp differs")


if __name__ == "__main__":
    unittest.main()
