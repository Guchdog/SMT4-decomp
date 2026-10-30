import unittest

from tools.h2_script_step_experiment import (
    EXPECTED,
    OPCODES,
    SCENARIOS,
    compare,
    handler_stub,
)


class H2ScriptStepExperimentTests(unittest.TestCase):
    def test_scenarios_cover_all_dispatched_result_classes(self):
        self.assertEqual(set(value for seq in SCENARIOS.values() for value in seq),
                         {0, 1, 2, 3, 255})
        self.assertEqual(set(OPCODES), {0, 1, 2, 3, 255})

    def test_result_zero_terminates_with_status_two_and_clears_d0(self):
        self.assertEqual(EXPECTED["zero_terminates"],
                         {"return": 2, "index": 1, "cc": 0x13, "d0": 0, "calls": 1})

    def test_result_two_increments_both_counters_and_returns_one(self):
        self.assertEqual(EXPECTED["two_returns_one"],
                         {"return": 1, "index": 1, "cc": 0x14, "d0": 0x22, "calls": 1})

    def test_result_one_and_other_nonzero_continue_until_terminal_callback(self):
        self.assertEqual(SCENARIOS["other_then_one_then_two"], [3, 1, 2])
        self.assertEqual(EXPECTED["other_then_one_then_two"]["index"], 3)
        self.assertEqual(EXPECTED["one_then_zero"]["return"], 2)

    def test_synthetic_handler_advances_index_and_records_calls(self):
        code = handler_stub(2)
        self.assertEqual(len(code), 32)
        self.assertEqual(len(handler_stub(1, advance=False)), 20)

    def test_comparator_detects_work_or_return_drift(self):
        original = {"fault": None, "completed": True, "return": 2, "pc": 0x1000,
                    "sp": 0x8000, "preserved": {"r4": True}, "work": "same"}
        self.assertIsNone(compare(original, dict(original)))
        self.assertEqual(compare(original, dict(original, **{"return": 1})), "return differs")
        self.assertEqual(compare(original, dict(original, **{"work": "changed"})), "work differs")


if __name__ == "__main__":
    unittest.main()
