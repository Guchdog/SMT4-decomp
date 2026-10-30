from __future__ import annotations

import unittest

from tools.h2_apt_utility4_inplace_runtime_probe import (
    CANDIDATE_BODY_SIZE,
    candidate_delta,
    mark_software_breakpoint_cleared,
    wrapper_arguments,
)


class RuntimeProbeContractTests(unittest.TestCase):
    def test_wrapper_arguments_include_both_stack_words(self):
        regs = {f"r{i}": value for i, value in enumerate((4, 0, 0, 0))}
        self.assertEqual(wrapper_arguments(regs, [0, 0]), [4, 0, 0, 0, 0, 0])

    def test_wrapper_argument_negative_control_changes_command(self):
        regs = {f"r{i}": value for i, value in enumerate((5, 0, 0, 0))}
        self.assertNotEqual(wrapper_arguments(regs, [0, 0]), [4, 0, 0, 0, 0, 0])

    def test_candidate_delta_accepts_only_exact_body_range(self):
        base = bytearray(64)
        final = bytearray(base)
        final[10] = 1
        result = candidate_delta(bytes(base), bytes(final), 10)
        self.assertEqual(result["changed_byte_count"], 1)
        self.assertTrue(result["all_changes_inside_candidate_body"])

    def test_candidate_delta_flags_byte_outside_declared_body(self):
        base = bytearray(CANDIDATE_BODY_SIZE + 2)
        final = bytearray(base)
        final[-1] = 1
        result = candidate_delta(bytes(base), bytes(final), 0)
        self.assertFalse(result["all_changes_inside_candidate_body"])

    def test_wrapper_breakpoint_clear_is_recorded_after_acknowledgement(self):
        capture = {"software_breakpoints": [{"address": "0x002b5a1c", "set": True, "cleared": False}]}
        mark_software_breakpoint_cleared(capture, 0x002B5A1C)
        self.assertTrue(capture["software_breakpoints"][0]["cleared"])
        self.assertTrue(capture["software_breakpoints"][0]["clear_acknowledged"])

    def test_breakpoint_clear_rejects_an_unrecorded_address(self):
        capture = {"software_breakpoints": []}
        with self.assertRaises(RuntimeError):
            mark_software_breakpoint_cleared(capture, 0x002B5A1C)


if __name__ == "__main__":
    unittest.main()
