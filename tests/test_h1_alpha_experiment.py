import unittest

from tools import h1_alpha_experiment as experiment


class H1AlphaExperimentTests(unittest.TestCase):
    def test_case_matrix_covers_signed_gate_and_alias_routes(self):
        cases = experiment.make_cases(20261025)
        self.assertEqual(len(cases), 288)
        directed = cases[:160]
        self.assertEqual(
            {int.from_bytes(case["data"][0x234:0x238], "little", signed=True)
             for case in directed},
            {-0x80000000, -1, 0, 1, 0x7FFFFFFF},
        )
        # The pointer at child+0x4c is null, external, or aliases the child
        # alpha/pointer slots; these cover both branch and alias ordering.
        pointers = {int.from_bytes(case["data"][0x24C:0x250], "little")
                    for case in directed}
        self.assertIn(0, pointers)
        self.assertIn(experiment.DATA + 0x200 + 0x38, pointers)
        self.assertIn(experiment.DATA + 0x200 + 0x0C, pointers)

    def test_compare_checks_memory_and_callee_saved_registers(self):
        state = {
            "stopped": True, "fault": None, "gp": [0] * 13,
            "sp": 1, "fpscr": 2, "fpexc": 3,
            "s": [0] * 32, "data": b"data", "stack": b"stack",
            "reads": frozenset(), "writes": frozenset(),
        }
        self.assertIsNone(experiment.compare(state, dict(state)))
        changed = dict(state)
        changed["gp"] = list(state["gp"])
        changed["gp"][4] = 1
        self.assertEqual(experiment.compare(state, changed), "callee-saved r4")
        changed = dict(state)
        changed["data"] = b"diff"
        self.assertEqual(experiment.compare(state, changed), "data")


if __name__ == "__main__":
    unittest.main()
