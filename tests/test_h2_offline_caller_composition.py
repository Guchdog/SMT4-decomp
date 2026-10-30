import unittest

from tools.h2_offline_caller_composition import (
    CALC_CALLBACK,
    arm_branch,
    compare_runs,
    make_candidate_negative_control,
    scenario_specs,
    validate_reset_arguments,
)


def reset_trace():
    items = [
        ("0x002b8b78", "0x01004010", ["0x00000099", "0x02002150", "0x00000000", "0x00000001"], None),
        ("0x002b8b78", "0x001ea3f0", ["0x0000009f", "0x51520101", "0x51530202", "0x51540303"], None),
        ("0x002b88c4", "0x001ea3fc", ["0x00000011", "0x00000014", "0x51530202", "0x51540303"], None),
        ("0x002b88c4", "0x001ea40c", ["0x00000011", "0x00000015", "0x51530202", "0x51540303"], None),
        ("0x002b88c4", "0x001ea41c", ["0x00000011", "0x00000018", "0x51530202", "0x51540303"], None),
        ("0x002b88c4", "0x001ea42c", ["0x00000011", "0x00000019", "0x51530202", "0x51540303"], None),
        ("0x00275e58", "0x001ea440", ["0x00000002", "0x00000000", "0x00000000", "0x00000000"], None),
        ("0x002a0c54", "0x001ea454", ["0x00407ef4", "0x00000000", "0x00000000", "0x00000000"], "title/title_top.bcenv"),
        ("0x002a06dc", "0x001ea464", ["0xcafe0088", "0x00000000", "0x00000000", "0x00000000"], None),
    ]
    return [{"address": addr, "call_site": site, "r0_r3": regs, "r0_string": string}
            for addr, site, regs, string in items]


class CallerCompositionTests(unittest.TestCase):
    def test_scenarios_use_distinct_config_and_flag_gate(self):
        baseline, distinct, gate = scenario_specs()
        self.assertNotEqual(baseline["config"], distinct["config"])
        self.assertEqual(len(baseline["config"]), 8)
        self.assertEqual(len(distinct["config"]), 8)
        self.assertEqual(gate["flag_7c"], 1)
        self.assertEqual(gate["active_sequence"], [])

    def test_arm_branch_encodes_and_rejects_misalignment(self):
        self.assertEqual(arm_branch(0x1000, 0x1008), b"\x00\x00\x00\xea")
        with self.assertRaises(ValueError):
            arm_branch(0x1000, 0x1009)

    def test_wrong_callback_mutant_changes_only_the_expected_literal(self):
        prefix = b"prefix"
        body = prefix + CALC_CALLBACK.to_bytes(4, "little") + b"suffix"
        mutant, meta = make_candidate_negative_control(body)
        self.assertEqual(mutant[:len(prefix)], prefix)
        self.assertEqual(int.from_bytes(mutant[len(prefix):len(prefix) + 4], "little"),
                         CALC_CALLBACK + 4)
        self.assertEqual(meta["literal_offset"], hex(len(prefix)))
        with self.assertRaises(ValueError):
            make_candidate_negative_control(body + body)

    def test_factory_tuple_difference_is_a_differential_failure(self):
        record = {"r0_string": "TITLE_CONFIG_MAIN",
                  "stack_words": ["0", "0x001ea928", "0x002caef0", "0x02002000"],
                  "hle_return": "0x01110001"}
        wrong = {**record, "stack_words": ["0", "0x001ea92c", "0x002caef0", "0x02002000"]}
        run = {"fault": None, "hook_error": None, "phases": [], "task_records": [record]}
        mutant = {**run, "task_records": [wrong]}
        self.assertEqual(compare_runs(run, mutant),
                         "process-factory callback/work/task tuple differs")

    def test_reset_argument_mismatch_fails_validation(self):
        trace = reset_trace()
        self.assertIsNone(validate_reset_arguments(trace))
        trace[2]["r0_r3"][1] = "0x00000015"
        self.assertIn("reset consumed arguments mismatch at 0x001ea3fc",
                      validate_reset_arguments(trace))

    def test_sound_playse_consumes_r0_and_keeps_r1_as_diagnostic(self):
        trace = reset_trace()
        trace[0]["r0_r3"][1] = "0x002b8b78"
        self.assertIsNone(validate_reset_arguments(trace))
        trace[0]["r0_r3"][0] = "0x00000098"
        self.assertIn("Sound_PlaySE consumed se_id sequence differs",
                      validate_reset_arguments(trace))


if __name__ == "__main__":
    unittest.main()
