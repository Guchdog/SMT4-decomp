from __future__ import annotations

import time
import unittest
from pathlib import Path

from tools.h1_navigation_adapter_experiment import (
    GATE_EXIT, ROOT, TOUCH_STOP, run_experiment,
)


class TestH1NavigationAdapterExperiment(unittest.TestCase):
    def test_tail_adapter_rejoins_original_callback_with_captured_context(self):
        code = ROOT / "extracted/exefs/code.bin"
        self.assertTrue(code.is_file(), "pinned private code.bin is required")
        private_checks = (ROOT / "build/agent-work/H1-semantic/"
                          "h1-navigation-adapter-differential/sleep-20261025-nav-adapter-diff-v2/checks")
        private_checks.mkdir(parents=True, exist_ok=True)
        output = private_checks / f"unittest-{time.time_ns()}"
        report = run_experiment(code, output)

        self.assertTrue(report["passed"])
        self.assertEqual(len(report["cases"]), 5)
        self.assertTrue(all(case["passed"] for case in report["cases"]))
        self.assertTrue(all(case["sp_aligned"] for case in report["cases"]))
        self.assertEqual([case["adapter_stop"] for case in report["cases"][:2]],
                         [hex(GATE_EXIT), hex(GATE_EXIT)])
        self.assertTrue(all(case["adapter_stop"] == hex(TOUCH_STOP)
                            for case in report["cases"][2:]))

        mutation = report["cases"][-1]
        self.assertEqual(mutation["original_r4"], "0x2000100")
        self.assertEqual(mutation["adapter_r4"], "0x2000100")
        self.assertEqual(mutation["adapter_r8"], "0x44e300")
        self.assertEqual(mutation["adapter_s17"], "0x3f800000")
        self.assertEqual(mutation["adapter_r6"], "0x2000300")
        self.assertEqual(mutation["mailbox"], "0x2000100")
        self.assertEqual(mutation["slot"], "0x2000300")

        changed = report["selected_trace"]["changed-selection-event-and-blend-clamp"]["adapter_timeline"]
        event = next(row for row in changed if row["kind"] == "event")
        self.assertEqual(event, {"kind": "event", "event_id": 0x0100016C,
                                 "selection": 2, "cached": 0})

        controls = report["control_results"]
        self.assertTrue(all(item["rejected"] for item in controls.values()))
        self.assertEqual(controls["wrong_status_target"]["candidate_stop"], hex(TOUCH_STOP))
        self.assertTrue(controls["missing_s17_restore"]["s17_differ"])
        self.assertTrue(controls["reload_instead_of_captured_pointer"]["r4_differ"])
        self.assertEqual(report["evidence"]["runtime"], "not_run")


if __name__ == "__main__":
    unittest.main()
