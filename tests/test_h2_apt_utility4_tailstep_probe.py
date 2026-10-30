import unittest
from unittest.mock import patch

from tools import h2_apt_utility4_tailstep_probe as probe


class FakeRsp:
    def __init__(self, stepped=b"T05;thread:1;"):
        self.commands = []
        self.stepped = stepped

    def request(self, command, expected=None):
        self.commands.append(command)
        result = self.stepped if command == b"s" else b"OK"
        if expected is not None and result != expected:
            raise AssertionError("unexpected fake reply")
        return result


class CaptureSocket:
    def __init__(self, commands):
        self.closed = False
        self.commands = commands

    def close(self):
        self.closed = True
        self.commands.append(b"<socket-close>")


class CaptureRsp:
    def __init__(self, failure):
        self.failure = failure
        self.commands = []
        self.sock = CaptureSocket(self.commands)

    def set_deadline(self, deadline):
        pass

    def begin_cleanup_grace(self):
        pass

    def request(self, command, expected=None):
        self.commands.append(command)
        if command == self.failure:
            raise probe.base.DeadlineExpired("simulated lost reply")
        if command.startswith(b"qSupported"):
            reply = b"multiprocess+;swbreak+"
        elif command == b"qfProcessInfo":
            reply = b"pid:b;"
        elif command.startswith(b"vAttach;"):
            reply = b"T05;thread:1;"
        else:
            reply = b"OK"
        if expected is not None and reply != expected:
            raise AssertionError("unexpected fake reply")
        return reply


def registers(pc, lr=0x00103E84, sp=0x0FFFFF00):
    result = {f"r{i}": 0 for i in range(16)}
    result.update(r15=pc, r14=lr, r13=sp)
    return result


class TailStepTests(unittest.TestCase):
    def test_pinned_static_branch_contract(self):
        raw = (probe.base.ROOT / probe.base.CODE_REL).read_bytes()
        result = probe.verify_tail_contract(raw)
        self.assertEqual(result["branch"], "0x002c5638")
        self.assertEqual(result["destination"], "0x002c0efc")

    def test_one_hit_removes_breakpoint_and_steps_same_thread(self):
        rsp = FakeRsp()
        with patch.object(probe.base, "continue_until_stop", return_value=(b"T05;thread:1;", "stopped")), \
             patch.object(probe.base, "read_registers", side_effect=[registers(probe.ENTRY), registers(probe.TARGET)]):
            hits, reason = probe.collect_one_step(rsp, 1, deadline=100.0)
        self.assertEqual(reason, "max_hits_reached")
        self.assertEqual(hits[0]["step"]["pc_after"], "0x002c0efc")
        self.assertEqual(rsp.commands, [b"Hg1", b"z0,2c5638,4", b"Hc1", b"s", b"Hg1"])
        self.assertTrue(all(not command.startswith((b"M", b"P", b"X")) for command in rsp.commands))

    def test_rejects_wrong_thread_or_destination(self):
        for stepped, after, message in ((b"T05;thread:2;", registers(probe.TARGET), "different thread"),
                                         (b"T05;thread:1;", registers(probe.TARGET + 4), "expected target")):
            rsp = FakeRsp(stepped)
            with patch.object(probe.base, "continue_until_stop", return_value=(b"T05;thread:1;", "stopped")), \
                 patch.object(probe.base, "read_registers", side_effect=[registers(probe.ENTRY), after]):
                with self.assertRaisesRegex(probe.base.ProbeError, message):
                    probe.collect_one_step(rsp, 1, deadline=100.0)

    def test_requires_one_hit_and_thread_identity(self):
        self.assertEqual(probe.require_one_hit(1), 1)
        with self.assertRaisesRegex(probe.base.ProbeError, "exactly one"):
            probe.require_one_hit(4)
        with self.assertRaisesRegex(probe.base.ProbeError, "thread ID"):
            probe.stop_thread(b"T05")
        with self.assertRaisesRegex(probe.base.ProbeError, "SIGTRAP"):
            probe.stop_thread(b"T0b;thread:1;")

    def test_lost_step_reply_runs_inherited_cleanup(self):
        rsp = CaptureRsp(b"s")
        with patch.multiple(probe.base, BREAKPOINT=probe.ENTRY,
                            validate_max_hits=probe.require_one_hit,
                            collect_hits=probe.collect_one_step), \
             patch.object(probe.base, "continue_until_stop", return_value=(b"T05;thread:1;", "stopped")), \
             patch.object(probe.base, "read_registers", return_value=registers(probe.ENTRY)):
            with self.assertRaisesRegex(probe.base.ProbeError, "lost reply"):
                probe.base.capture_session(rsp, 1, deadline=100.0)
        self.assertEqual(rsp.commands.count(b"z0,2c5638,4"), 2)
        self.assertIn(b"D", rsp.commands)
        self.assertTrue(rsp.sock.closed)

    def test_lost_breakpoint_reply_detaches_but_cannot_claim_restoration(self):
        rsp = CaptureRsp(b"Z0,2c5638,4")
        with patch.multiple(probe.base, BREAKPOINT=probe.ENTRY,
                            validate_max_hits=probe.require_one_hit,
                            collect_hits=probe.collect_one_step):
            with self.assertRaisesRegex(probe.base.ProbeError, "lost reply"):
                probe.base.capture_session(rsp, 1, deadline=100.0)
        self.assertNotIn(b"z0,2c5638,4", rsp.commands)
        self.assertIn(b"D", rsp.commands)
        self.assertTrue(rsp.sock.closed)

    def test_production_fatal_callback_kills_before_disconnect_for_lost_replies(self):
        for failure in (b"Z0,2c5638,4", b"z0,2c5638,4", b"s"):
            with self.subTest(failure=failure):
                rsp = CaptureRsp(failure)
                def stop_child():
                    rsp.commands.append(b"<child-stopped>")
                with patch.multiple(probe.base, BREAKPOINT=probe.ENTRY,
                                    validate_max_hits=probe.require_one_hit,
                                    collect_hits=probe.collect_one_step), \
                     patch.object(probe.base, "continue_until_stop", return_value=(b"T05;thread:1;", "stopped")), \
                     patch.object(probe.base, "read_registers", return_value=registers(probe.ENTRY)):
                    with self.assertRaisesRegex(probe.base.ProbeError, "lost reply"):
                        probe.base.capture_session(rsp, 1, deadline=100.0, on_fatal=stop_child)
                self.assertNotIn(b"D", rsp.commands)
                self.assertLess(rsp.commands.index(b"<child-stopped>"), rsp.commands.index(b"<socket-close>"))

    def test_lost_cleanup_z0_stops_child_before_detach(self):
        rsp = CaptureRsp(b"z0,2c5638,4")
        def stop_child():
            rsp.commands.append(b"<child-stopped>")
        with patch.multiple(probe.base, BREAKPOINT=probe.ENTRY,
                            validate_max_hits=probe.require_one_hit), \
             patch.object(probe.base, "collect_hits", return_value=([{}], "max_hits_reached")):
            with self.assertRaisesRegex(probe.base.ProbeError, "breakpoint clear"):
                probe.base.capture_session(rsp, 1, deadline=100.0, on_fatal=stop_child)
        self.assertNotIn(b"D", rsp.commands)
        self.assertLess(rsp.commands.index(b"<child-stopped>"), rsp.commands.index(b"<socket-close>"))

    def test_failed_child_stop_preserves_socket_and_reports_both_errors(self):
        rsp = CaptureRsp(b"Z0,2c5638,4")
        def stop_child():
            raise RuntimeError("cannot stop child")
        with patch.multiple(probe.base, BREAKPOINT=probe.ENTRY,
                            validate_max_hits=probe.require_one_hit,
                            collect_hits=probe.collect_one_step):
            with self.assertRaisesRegex(probe.base.ProbeError, "lost reply.*cannot stop child"):
                probe.base.capture_session(rsp, 1, deadline=100.0, on_fatal=stop_child)
        self.assertNotIn(b"D", rsp.commands)
        self.assertFalse(rsp.sock.closed)


if __name__ == "__main__":
    unittest.main()
