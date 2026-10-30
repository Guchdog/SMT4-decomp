import unittest

from tools.h2_calc_experiment import Scenario
from tools.h2_calc_sequence_experiment import (
    EXPECTED_ORIGINAL_SHA256, _assert_tick, compare_tick, sequence_specs,
)
import struct


class CalcSequenceTests(unittest.TestCase):
    def test_sequences_cover_required_states_and_branches(self):
        specs = sequence_specs(7)
        labels = {spec["label"] for spec in specs}
        self.assertIn("state0-wait-ready-state1-entry", labels)
        self.assertIn("state1-logical-actions-and-clamps", labels)
        self.assertIn("state2-exit-result-0", labels)
        self.assertIn("state2-exit-result-1", labels)
        self.assertIn("state2-exit-result-2", labels)
        self.assertIn("state2-exit-result-3", labels)
        clamp = next(spec for spec in specs if spec["label"] == "state1-logical-actions-and-clamps")
        self.assertEqual(clamp["steps"][1]["logical"], {(4, 0): 1})
        self.assertEqual(clamp["steps"][2]["logical"], {(4, 0): 1})
        self.assertEqual(clamp["steps"][3]["logical"], {(3, 0): 1})
        self.assertEqual(clamp["steps"][1]["work_values"], {0: 0})
        self.assertEqual(clamp["steps"][2]["work_values"], {0: 0})

    def test_seed_passes_have_distinct_valid_option_fixtures(self):
        seven = next(s for s in sequence_specs(7) if s["label"] == "state0-wait-ready-state1-entry")
        other = next(s for s in sequence_specs(20261024) if s["label"] == "state0-wait-ready-state1-entry")
        self.assertNotEqual(seven["steps"][0]["scenario"].values[2],
                            other["steps"][0]["scenario"].values[2])
        self.assertTrue(2 <= seven["steps"][0]["scenario"].values[2] <= 9)
        self.assertTrue(2 <= other["steps"][0]["scenario"].values[2] <= 9)

    def test_comparator_detects_different_config_and_work(self):
        base = {"fault": None, "stopped": True, "preserved": (1,), "expected_preserved": (1,),
                "image_sha256": EXPECTED_ORIGINAL_SHA256, "return": 0, "pc": 0x1000, "work": b"a",
                "config": b"b", "work_global": b"c", "config_global": b"d", "trace": []}
        changed = {**base, "work": b"changed"}
        self.assertEqual(compare_tick(base, changed), "work differs")

    def test_scenario_clone_does_not_infer_physical_button_labels(self):
        scenario = Scenario("logical-decrement", 1, logical={(4, 0): 1})
        self.assertEqual(scenario.logical, {(4, 0): 1})

    def test_lower_bound_assertion_rejects_underflow_or_wrong_value(self):
        step = {"expect_state": 1, "work_values": {0: 0}}
        for value in (0xFFFFFFFF, 1):
            work = bytearray(0x158)
            struct.pack_into("<I", work, 0x08, 1)
            struct.pack_into("<I", work, 0x28, value)
            result = {"fault": None, "stopped": True, "preserved": (),
                      "expected_preserved": (), "state": 1, "work": bytes(work)}
            self.assertIn("option[0]", _assert_tick(result, step, "patched"))


if __name__ == "__main__":
    unittest.main()
