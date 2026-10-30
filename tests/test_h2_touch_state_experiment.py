import unittest

from tools.h2_touch_state_experiment import (
    ACTIVE_VALUES,
    STATE_VALUES,
    compare,
    expected,
)


class H2TouchStateExperimentTests(unittest.TestCase):
    def test_getter_returns_state_only_for_matching_signed_handle(self):
        self.assertEqual(expected(-1, -1, 6), 6)
        self.assertEqual(expected(10, 10, 255), 255)
        self.assertEqual(expected(11, 10, 6), 0)

    def test_zero_state_remains_zero_on_a_match(self):
        self.assertEqual(expected(-32768, -32768, 0), 0)

    def test_matrix_covers_signed_boundaries_and_h2_registration_indices(self):
        self.assertEqual(
            ACTIVE_VALUES,
            (-32768, -1, 0, 1, 9, 10, 11, 12, 32767),
        )
        self.assertEqual(65_536 * len(ACTIVE_VALUES), 589_824)
        self.assertEqual(STATE_VALUES, (0, 1, 2, 6, 255))
        self.assertEqual(len(ACTIVE_VALUES) * len(STATE_VALUES), 45)

    def test_comparator_accepts_matching_abi_and_effect_observations(self):
        state = {"fault": None, "return": 6, "pc": 0x1000, "sp": 0x8000,
                 "preserved": {"r4": True, "r11": True}}
        self.assertIsNone(compare(state, dict(state)))

    def test_comparator_detects_mutant_that_ignores_active_index(self):
        original = {"fault": None, "return": 0, "pc": 0x1000, "sp": 0x8000,
                    "preserved": {"r4": True}}
        mutant = dict(original, **{"return": 6})
        self.assertEqual(compare(original, mutant), "return differs")

    def test_comparator_detects_fault_and_callee_saved_drift(self):
        original = {"fault": None, "return": 0, "pc": 0x1000, "sp": 0x8000,
                    "preserved": {"r4": True}}
        self.assertEqual(compare(original, dict(original, fault="fault")), "fault differs")
        self.assertEqual(
            compare(original, dict(original, preserved={"r4": False})),
            "preserved differs",
        )


if __name__ == "__main__":
    unittest.main()
