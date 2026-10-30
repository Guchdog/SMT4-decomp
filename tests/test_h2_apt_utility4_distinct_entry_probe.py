import unittest
from unittest.mock import patch

from tools import h2_apt_utility4_distinct_entry_probe as probe
from tests.test_h2_apt_utility4_tailstep_probe import FakeRsp, registers


class DistinctEntryTests(unittest.TestCase):
    def test_timeout_after_first_hit_returns_partial_with_breakpoint_reinserted(self):
        rsp = FakeRsp()
        with patch.object(probe.base, "continue_until_stop", side_effect=[(b"T05;thread:1;", "stopped"), (None, "capture_timeout")]), \
             patch.object(probe.base, "read_registers", side_effect=[registers(probe.ENTRY), registers(probe.AFTER_FIRST_INSTRUCTION)]):
            hits, reason = probe.collect_distinct_entries(rsp, 2, deadline=100.0)
        self.assertEqual(reason, "capture_timeout")
        self.assertEqual(len(hits), 1)
        self.assertTrue(hits[0]["step"]["breakpoint_reinserted"])
        self.assertIn(b"Z0,2c0efc,4", rsp.commands)

    def test_two_hits_step_past_breakpoint_before_next_continue(self):
        rsp = FakeRsp()
        before1 = registers(probe.ENTRY, lr=0x00103E84)
        after1 = registers(probe.AFTER_FIRST_INSTRUCTION, lr=0x00103E84)
        before2 = registers(probe.ENTRY, lr=0x002C0F70)
        after2 = registers(probe.AFTER_FIRST_INSTRUCTION, lr=0x002C0F70)
        with patch.object(probe.base, "continue_until_stop", side_effect=[(b"T05;thread:1;", "stopped"), (b"T05;thread:1;", "stopped")]), \
             patch.object(probe.base, "read_registers", side_effect=[before1, after1, before2, after2]):
            hits, reason = probe.collect_distinct_entries(rsp, 2, deadline=100.0)
        self.assertEqual(reason, "max_hits_reached")
        self.assertEqual([hit["lr"]["lr"] for hit in hits], ["0x00103e84", "0x002c0f70"])
        self.assertTrue(hits[0]["step"]["breakpoint_reinserted"])
        self.assertFalse(hits[1]["step"]["breakpoint_reinserted"])
        self.assertEqual(rsp.commands, [b"Hg1", b"z0,2c0efc,4", b"Hc1", b"s", b"Hg1", b"Z0,2c0efc,4",
                                        b"Hg1", b"z0,2c0efc,4", b"Hc1", b"s", b"Hg1"])
        self.assertTrue(all(not c.startswith((b"M", b"P", b"X")) for c in rsp.commands))

    def test_rejects_wrong_step_pc_and_thread(self):
        for stepped, after, message in ((b"T05;thread:2;", registers(probe.AFTER_FIRST_INSTRUCTION), "different thread"),
                                         (b"T05;thread:1;", registers(probe.ENTRY), "advance one ARM instruction")):
            rsp = FakeRsp(stepped)
            with patch.object(probe.base, "continue_until_stop", return_value=(b"T05;thread:1;", "stopped")), \
                 patch.object(probe.base, "read_registers", side_effect=[registers(probe.ENTRY), after]):
                with self.assertRaisesRegex(probe.base.ProbeError, message):
                    probe.collect_distinct_entries(rsp, 1, deadline=100.0)

    def test_reinsertion_failure_propagates_and_hit_bound_is_enforced(self):
        class FailingRsp(FakeRsp):
            def request(self, command, expected=None):
                if command.startswith(b"Z0,"):
                    raise probe.base.DeadlineExpired("lost reinsertion reply")
                return super().request(command, expected)
        rsp = FailingRsp()
        with patch.object(probe.base, "continue_until_stop", return_value=(b"T05;thread:1;", "stopped")), \
             patch.object(probe.base, "read_registers", side_effect=[registers(probe.ENTRY), registers(probe.AFTER_FIRST_INSTRUCTION)]):
            with self.assertRaisesRegex(probe.base.DeadlineExpired, "reinsertion"):
                probe.collect_distinct_entries(rsp, 2, deadline=100.0)
        with self.assertRaises(probe.base.ProbeError):
            probe.collect_distinct_entries(FakeRsp(), 5, deadline=100.0)


if __name__ == "__main__":
    unittest.main()
