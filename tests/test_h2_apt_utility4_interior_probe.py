import unittest
from unittest.mock import patch

from tools import h2_apt_utility4_interior_probe as probe


class InteriorEntryTests(unittest.TestCase):
    def test_pinned_image_has_expected_direct_entries(self):
        raw = (probe.base.ROOT / probe.base.CODE_REL).read_bytes()
        result = probe.verify_interior_entry(raw)
        self.assertEqual(result["entry"], "0x002c0efc")
        self.assertEqual(len(result["direct_arm_bl"]), 3)
        self.assertEqual(len(result["direct_arm_tail_b"]), 4)
        changed = bytearray(raw)
        changed[probe.ENTRY - probe.base.CODE_BASE] ^= 1
        with self.assertRaisesRegex(probe.base.ProbeError, "identity mismatch"):
            probe.verify_interior_entry(bytes(changed))

    def test_tail_scan_distinguishes_b_from_bl(self):
        pc = probe.base.CODE_BASE
        displacement = (probe.ENTRY - (pc + 8)) >> 2
        b = (0xEA000000 | (displacement & 0xFFFFFF)).to_bytes(4, "little")
        bl = (0xEB000000 | (((probe.ENTRY - (pc + 12)) >> 2) & 0xFFFFFF)).to_bytes(4, "little")
        self.assertEqual(probe.direct_tail_branches(b + bl), [pc])

    def test_lr_labels_do_not_claim_tail_origin(self):
        self.assertEqual(probe.classify_entry_lr(0x002C0F70)["classification"], "consistent_with_direct_bl")
        self.assertEqual(probe.classify_entry_lr(0x00102188)["classification"], "consistent_with_ee0_fallthrough")
        unknown = probe.classify_entry_lr(0x12345678)
        self.assertEqual(unknown["classification"], "unresolved_possible_tail_or_indirect")
        self.assertIsNone(unknown["caller_callsite"])

    def test_runner_configuration_restricts_task_and_target(self):
        base = probe.base
        with patch.multiple(base, BREAKPOINT=base.BREAKPOINT,
                            EXPECTED_CALLER_ADDRESSES=base.EXPECTED_CALLER_ADDRESSES,
                            CALLERS=base.CALLERS, classify_lr=base.classify_lr,
                            TASK_ID=base.TASK_ID, RUNTIME_TASK_ID=base.RUNTIME_TASK_ID,
                            ALLOWED_TASK_IDS=base.ALLOWED_TASK_IDS,
                            static_contract=base.static_contract):
            probe.configure_runner()
            self.assertEqual(base.BREAKPOINT, probe.ENTRY)
            self.assertEqual(base.ALLOWED_TASK_IDS, {probe.TASK_ID, probe.RUNTIME_TASK_ID})
            self.assertEqual(base.EXPECTED_CALLER_ADDRESSES, probe.DIRECT_BL)


if __name__ == "__main__":
    unittest.main()
