import unittest

from tools.h2_ready_experiment import (
    CODE_BASE,
    CODE_MAP_SIZE,
    SCENARIOS,
    WORK,
    WORK_SIZE,
    compare,
    expected_ready,
    validate_workspace_layout,
)


class H2ReadyExperimentTests(unittest.TestCase):
    def test_ready_predicate_contract_boundaries(self):
        self.assertEqual(expected_ready(0, 0), 1)
        self.assertEqual(expected_ready(WORK, 1), 0)
        self.assertEqual(expected_ready(WORK, 0), 1)

    def test_fixture_is_outside_complete_code_mapping(self):
        validate_workspace_layout(CODE_BASE, CODE_MAP_SIZE, WORK, WORK_SIZE)
        self.assertGreaterEqual(WORK, CODE_BASE + CODE_MAP_SIZE)

    def test_overlapping_fixture_region_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "overlaps mapped pinned code image"):
            validate_workspace_layout(CODE_BASE, CODE_MAP_SIZE, 0x00410000, WORK_SIZE)

    def test_matrix_covers_global_and_task_lifecycle_boundaries(self):
        self.assertEqual(
            {case["label"] for case in SCENARIOS},
            {"null-global", "task-still-registered", "task-no-longer-registered",
             "null-task-handle-forwarded"},
        )

    def test_comparator_accepts_matching_observations(self):
        outcome = {"fault": None, "stopped": True,
                   "preserved": {"sp": True, "r4": True, "r5": True, "r6": True,
                                 "r7": True, "r8": True, "r9": True, "r10": True,
                                 "r11": True, **{f"d{i}": True for i in range(8, 16)}},
                   "return": 1, "pc": 0x01000FFC, "trace": []}
        self.assertIsNone(compare(outcome, dict(outcome)))

    def test_comparator_detects_return_drift(self):
        original = {"fault": None, "stopped": True, "preserved": {"sp": True, "r4": True},
                    "return": 0, "pc": 0x01000FFC, "trace": [{"task": "0x12345678"}]}
        candidate = dict(original, **{"return": 1})
        self.assertEqual(compare(original, candidate), "return differs")

    def test_comparator_rejects_abi_corruption(self):
        original = {"fault": None, "stopped": True, "preserved": {"sp": True, "r4": True},
                    "return": 1, "pc": 0x01000FFC, "trace": []}
        candidate = dict(original, **{"preserved": {"sp": False, "r4": True}})
        self.assertEqual(compare(original, candidate),
                         "candidate violated a callee-saved register or SP preservation")


if __name__ == "__main__":
    unittest.main()
