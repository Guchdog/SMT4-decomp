import unittest

from tools.h2_draw_experiment import DrawScenario, SERVICE_THUMB, compare, directed_scenarios


class H2DrawExperimentTests(unittest.TestCase):
    def test_matrix_covers_nonpositive_bounds_rows_and_touch_codes(self):
        cases = directed_scenarios()
        by_label = {case.label: case for case in cases}
        self.assertIn("row-count-zero", by_label)
        self.assertIn("row-count-negative", by_label)
        self.assertEqual(by_label["negative-absolute-index"].scroll, -1)
        self.assertEqual(by_label["negative-absolute-index"].row_count, 1)
        self.assertTrue(by_label["negative-absolute-index"].expect_no_tbb)
        self.assertEqual(by_label["absolute-index-three"].scroll, 3)
        self.assertEqual(by_label["absolute-index-three"].row_count, 1)
        self.assertTrue(by_label["absolute-index-three"].expect_no_tbb)
        for row in (0, 1, 2):
            self.assertIn(f"active-selected-row-{row}", by_label)
            for name in ("row", "decrement", "increment", "special"):
                handle = {"row": 0x110, "decrement": 0x111,
                          "increment": 0x112, "special": 0x113}[name]
                for code in (1, 2, 6):
                    scenario = by_label[f"active-row-{row}-{name}-touch-{code}"]
                    self.assertEqual(scenario.touches, {handle: code})

    def test_comparator_accepts_equal_records_and_detects_observable_drift(self):
        baseline = {
            "fault": None,
            "stopped": True,
            "preserved": (1, 2),
            "expected_preserved": (1, 2),
            "return": 0,
            "pc": 0x0100FFFC,
            "work": bytes(0x158),
            "config": bytes(8),
            "cache": bytes(0x80),
            "trace": [("panel_draw", 2, 0x2F, 3)],
        }
        self.assertIsNone(compare(baseline, dict(baseline)))
        for field in ("return", "pc", "work", "config", "cache", "trace"):
            changed = dict(baseline)
            changed[field] = b"changed" if isinstance(baseline[field], bytes) else "changed"
            self.assertEqual(compare(baseline, changed), f"{field} differs")

    def test_comparator_rejects_fault_or_abi_drift(self):
        baseline = {
            "fault": None,
            "stopped": True,
            "preserved": (1, 2),
            "expected_preserved": (1, 2),
            "return": 0,
            "pc": 4,
            "work": bytes(0x158),
            "config": bytes(8),
            "cache": bytes(0x80),
            "trace": [],
        }
        candidate = dict(baseline, fault="invalid memory read")
        self.assertEqual(compare(baseline, candidate), "candidate fault: invalid memory read")
        candidate = dict(baseline, preserved=(1, 3))
        self.assertEqual(compare(baseline, candidate),
                         "candidate violates callee-saved register/SP/d8-d15 ABI")

    def test_scenario_defaults_are_explicit(self):
        scenario = DrawScenario("fixture")
        self.assertEqual(scenario.state, 1)
        self.assertEqual(scenario.row_count, 3)
        self.assertEqual(scenario.selected_row, 0)
        self.assertEqual(scenario.scroll, 0)
        self.assertEqual(scenario.touches, {})

    def test_formatter_helper_is_the_only_thumb_service(self):
        self.assertEqual(SERVICE_THUMB, {0x002BE7FC: True})


if __name__ == "__main__":
    unittest.main()
