import unittest

from tools.h2_init_orchestration_experiment import (
    build_cases,
    compare,
    _trace_contract,
)


class H2InitOrchestrationTests(unittest.TestCase):
    def test_directed_baseline_distinct_config_and_ignored_argument(self):
        cases = build_cases(20261025, 2)
        self.assertEqual(cases[0]["config"], bytes.fromhex("3250503000000000"))
        self.assertEqual(cases[1]["config"], bytes.fromhex("0113273B4D5F7183"))
        self.assertNotEqual(cases[0]["arg"], cases[2]["arg"])
        self.assertNotEqual(cases[0]["config"], cases[2]["config"])
        self.assertEqual(len(cases), 5)

    def test_trace_projection_keeps_arguments_and_discards_scratch(self):
        record = {
            "address": "0x002c32f8", "name": "sprite_group_bind_original",
            "r0_r3": ["0x0200013c", "0x00407ec6", "0x18", "0"],
            "stack_words": ["0", "0", "0", "0", "0", "0", "0", "junk"],
            "s0_s3_bits": ["0", "0", "0", "scratch"],
        }
        noisy = dict(record)
        noisy["r0_r3"] = list(record["r0_r3"])
        noisy["r0_r3"][3] = "0xa5a50000"  # r3 is an argument here, so retained
        self.assertNotEqual(_trace_contract([record]), _trace_contract([noisy]))
        noisy["r0_r3"][3] = record["r0_r3"][3]
        noisy["stack_words"] = list(record["stack_words"])
        noisy["stack_words"][7] = "changed-unread-tail"
        self.assertEqual(_trace_contract([record]), _trace_contract([noisy]))

    def test_comparison_detects_targeted_memory_mutation(self):
        base = {"fault": None, "stopped": True, "return": 1, "pc": 2,
                "sp": 3, "preserved": [4], "trace": [], "global_work": "00",
                "work": "aa", "config": "bb", "writes": [1]}
        changed = dict(base)
        changed["work"] = "ab"
        self.assertEqual(compare(base, changed), "work differs")


if __name__ == "__main__":
    unittest.main()
