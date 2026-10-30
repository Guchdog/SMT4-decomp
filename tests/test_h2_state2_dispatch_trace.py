import struct
import unittest

from tools import h2_state2_dispatch_trace as trace


class MemoryRsp:
    def __init__(self):
        self.memory = {}

    def put(self, address, data):
        for offset, value in enumerate(data):
            self.memory[address + offset] = value

    def request(self, packet):
        if not packet.startswith(b"m"):
            raise AssertionError(f"unexpected RSP request: {packet!r}")
        address_text, size_text = packet[1:].decode().split(",", 1)
        address, size = int(address_text, 16), int(size_text, 16)
        return bytes(self.memory.get(address + i, 0) for i in range(size)).hex().encode()


class TimeoutSocket:
    def __init__(self):
        self.timeout = 30.0

    def gettimeout(self):
        return self.timeout

    def settimeout(self, value):
        self.timeout = value


class ContinueRsp:
    def __init__(self, raises=False):
        self.sock = TimeoutSocket()
        self.raises = raises
        self.timeout_seen = None

    def continue_to_stop(self):
        self.timeout_seen = self.sock.gettimeout()
        if self.raises:
            raise TimeoutError("socket wait expired")
        return b"T05"


class InterruptSocket(TimeoutSocket):
    def __init__(self):
        super().__init__()
        self.sent = []

    def sendall(self, data):
        self.sent.append(data)


class InterruptRsp(ContinueRsp):
    def __init__(self):
        super().__init__(raises=True)
        self.sock = InterruptSocket()

    def _packet(self):
        return b"T05thread:1;"


class ProgressRsp:
    def __init__(self):
        self.registers = {i: i + 0x10 for i in range(16)}
        self.registers[4] = 0x1000
        self.registers[14] = 0x001C05B8
        self.memory = {}
        self.put(0x1000, bytes.fromhex("4c002000000000000b00000000000000"))

    def put(self, address, data):
        for offset, value in enumerate(data):
            self.memory[address + offset] = value

    def request(self, packet):
        if packet.startswith(b"p"):
            register = int(packet[1:], 16)
            return struct.pack("<I", self.registers[register]).hex().encode()
        if packet.startswith(b"m"):
            address_text, size_text = packet[1:].decode().split(",", 1)
            address, size = int(address_text, 16), int(size_text, 16)
            return bytes(self.memory.get(address + i, 0) for i in range(size)).hex().encode()
        raise AssertionError(f"unexpected RSP request: {packet!r}")


class ReadTrackingProgressRsp(ProgressRsp):
    def __init__(self):
        super().__init__()
        self.memory_reads = []

    def request(self, packet):
        if packet.startswith(b"m"):
            address_text, size_text = packet[1:].decode().split(",", 1)
            self.memory_reads.append((int(address_text, 16), int(size_text, 16)))
        return super().request(packet)


class EpilogueRsp(ProgressRsp):
    def __init__(self):
        super().__init__()
        self.registers[4] = 0x10001000
        self.registers[13] = 0x10002000
        self.registers[15] = trace.BOOT_DISPATCH_EPILOGUE
        self.put(0x10001008, struct.pack("<I", trace.BOOT_COMMAND_RETURN_CONTEXT_WORD))
        self.put(0x10002000, struct.pack("<II", 0xDEADBEEF, trace.DISPATCH_CALLER_RETURN))


class ReturnStepRsp:
    def __init__(self):
        self.sock = TimeoutSocket()
        self.registers = {14: 0x00103164, 15: trace.DISPATCH_CALLER_RETURN}
        self.breakpoints = set()
        self.breakpoints_at_continue = None

    def request(self, packet):
        if packet.startswith(b"p"):
            register = int(packet[1:], 16)
            return struct.pack("<I", self.registers[register]).hex().encode()
        if packet.startswith(b"z0,"):
            _, address, _ = packet.decode().split(",")
            self.breakpoints.discard(int(address, 16))
            return b"OK"
        if packet.startswith(b"Z0,"):
            _, address, _ = packet.decode().split(",")
            self.breakpoints.add(int(address, 16))
            return b"OK"
        raise AssertionError(f"unexpected RSP request: {packet!r}")

    def continue_to_stop(self):
        self.breakpoints_at_continue = set(self.breakpoints)
        self.registers[15] = trace.DISPATCH_CALLER_NEXT
        return b"T05"


class BranchInputRsp(ReturnStepRsp):
    def __init__(self):
        super().__init__()
        self.registers.update({0: 1, 8: 0x14657380, 15: trace.DISPATCH_CALLER_NEXT})

    def continue_to_stop(self):
        self.breakpoints_at_continue = set(self.breakpoints)
        self.registers[15] = trace.DISPATCH_CALLER_BRANCH_INPUT
        return b"T05"


class ZeroBranchPathRsp(ReturnStepRsp):
    def __init__(self):
        super().__init__()
        self.registers.update({0: 0, 4: 0x14657380, 5: 0, 15: trace.DISPATCH_CALLER_BRANCH_INPUT})
        self.next_stops = [trace.DISPATCH_CALLER_ZERO_BRANCH_TARGET, trace.DISPATCH_CALLER_COMMON_HELPER_RETURN]
        self.breakpoints_at_continue_history = []

    def continue_to_stop(self):
        self.breakpoints_at_continue_history.append(set(self.breakpoints))
        self.registers[15] = self.next_stops.pop(0)
        if self.registers[15] == trace.DISPATCH_CALLER_COMMON_HELPER_RETURN:
            self.registers[0] = 0x1234
        return b"T05"


class State2DispatchTraceTests(unittest.TestCase):
    def test_task_fields_resolves_nested_method_id_and_callback(self):
        rsp = MemoryRsp()
        task = 0x1000
        method_table = 0x2000
        instruction_index = 12
        fields = bytearray(0xD4)
        struct.pack_into("<I", fields, 0x18, instruction_index)
        struct.pack_into("<I", fields, 0xBC, method_table)
        struct.pack_into("<I", fields, 0xCC, 9)
        struct.pack_into("<I", fields, 0xD0, 9)
        rsp.put(task, fields)
        rsp.put(method_table + 4 * instruction_index, struct.pack("<HH", 8, 6))
        rsp.put(trace.HANDLER_TABLE + 4 * 8, struct.pack("<I", trace.NESTED_WRAPPER))
        rsp.put(trace.NESTED_HANDLER_TABLE + 8 * 6, struct.pack("<I", 0x001ECBA4))

        result = trace.task_fields(rsp, task)

        self.assertEqual(result["handler_id"], 8)
        self.assertEqual(result["handler_target_raw"], "0x1a07cc")
        self.assertEqual(result["nested_handler_id"], 6)
        self.assertEqual(result["nested_handler_target_raw"], "0x1ecba4")
        self.assertEqual(result["instruction_index"], instruction_index)
        self.assertEqual((result["counter_cc"], result["counter_d0"]), (9, 9))

    def test_nested_return_cap_ignores_unreturned_calls(self):
        trace_data = {
            "nested_callbacks": ([{"phase": "return"}] * 19) + [{"phase": "call"}]
        }
        self.assertEqual(trace.nested_callback_return_count(trace_data), 19)
        self.assertFalse(trace.nested_callback_return_cap_reached(trace_data))
        trace_data["nested_callbacks"].append({"phase": "return"})
        self.assertEqual(trace.nested_callback_return_count(trace_data), 20)
        self.assertTrue(trace.nested_callback_return_cap_reached(trace_data))

    def test_pre_title_mode1_query_is_passed_through_only_at_observed_wrapper_call(self):
        self.assertTrue(
            trace.pass_through_pre_title_mode1_query(
                0, trace.TRIGGER2, trace.PRE_TITLE_MODE1_RETURN
            )
        )
        self.assertFalse(
            trace.pass_through_pre_title_mode1_query(
                0x15C00080, trace.TRIGGER2, trace.PRE_TITLE_MODE1_RETURN
            )
        )
        self.assertFalse(
            trace.pass_through_pre_title_mode1_query(
                0, trace.TRIGGER, trace.PRE_TITLE_MODE1_RETURN
            )
        )
        self.assertFalse(
            trace.pass_through_pre_title_mode1_query(
                0, trace.TRIGGER2, 0x001EA188
            )
        )

    def test_pre_title_original_query_evidence_is_aggregated_by_observation(self):
        summary = {"calls": 0, "groups": {}}
        sample = {
            "id": 0,
            "wrapper_caller_return_raw": "0x10edfc",
            "wrapper_caller_name": "camp_func_0010edd4",
            "return": 0,
            "mode_word_before": "0x0",
            "counter_before": "0x0",
        }

        trace.record_pre_title_query(summary, sample)
        trace.record_pre_title_query(summary, sample)
        trace.record_pre_title_query(summary, {**sample, "id": 1})

        self.assertEqual(summary["calls"], 3)
        self.assertEqual(len(summary["groups"]), 2)
        self.assertEqual(
            summary["groups"]["0|0x10edfc|0|0x0|0x0"]["count"], 2
        )

    def test_title_query_breakpoints_are_deferred_until_title_main_init(self):
        self.assertEqual(trace.title_query_breakpoints_for_phase(False), ())
        self.assertEqual(
            trace.title_query_breakpoints_for_phase(True),
            (trace.TRIGGER, trace.TRIGGER2),
        )

    def test_continue_uses_remaining_phase_deadline_and_restores_packet_timeout(self):
        rsp = ContinueRsp()
        deadline = __import__("time").monotonic() + 2.0

        self.assertEqual(
            trace.continue_until_deadline(rsp, deadline, "startup"), b"T05"
        )
        self.assertGreater(rsp.timeout_seen, 1.0)
        self.assertEqual(rsp.sock.gettimeout(), 30.0)

    def test_continue_deadline_reports_timeout_and_restores_packet_timeout(self):
        rsp = ContinueRsp(raises=True)
        deadline = __import__("time").monotonic() + 2.0

        with self.assertRaisesRegex(trace.TraceError, "startup wall-clock bound"):
            trace.continue_until_deadline(rsp, deadline, "startup")
        self.assertEqual(rsp.sock.gettimeout(), 30.0)

    def test_continue_deadline_interrupts_guest_and_keeps_stop_packet(self):
        rsp = InterruptRsp()
        deadline = __import__("time").monotonic() + 2.0

        with self.assertRaises(trace.TraceDeadlineError) as raised:
            trace.continue_until_deadline(rsp, deadline, "startup")

        self.assertEqual(raised.exception.interrupt_stop_reply, b"T05thread:1;")
        self.assertIsNone(raised.exception.interrupt_error)
        self.assertEqual(rsp.sock.sent, [b"\x03"])
        self.assertEqual(rsp.sock.gettimeout(), 30.0)

    def test_script_progress_snapshot_keeps_unresolved_context_word_unlabeled(self):
        rsp = ProgressRsp()
        result = trace.script_progress_snapshot(rsp, 0x001C05B8, 1.25)

        self.assertEqual(result["phase"], "after-map-script-resource-init")
        self.assertEqual(result["pc"], "0x1c05b8")
        self.assertEqual(result["context_pointer"], "0x1000")
        self.assertEqual(result["context_word_plus_8"], 11)
        self.assertNotIn("opcode_index", result)
        self.assertEqual(result["elapsed_s"], 1.25)

    def test_timeout_guest_snapshot_records_pc_registers_and_bounded_stack(self):
        rsp = ProgressRsp()
        rsp.registers[13] = 0x10002000
        rsp.registers[14] = 0x00103164
        rsp.registers[15] = 0x001C03D0
        rsp.put(0x10002000, bytes(range(0x80)))
        rsp.put(0x001C03D0, bytes.fromhex("0000a0e31e80bde8"))

        result = trace.timeout_guest_snapshot(rsp, b"T05thread:1;")

        self.assertEqual(result["pc"], "0x1c03d0")
        self.assertEqual(result["lr"], "0x103164")
        self.assertEqual(result["sp"], "0x10002000")
        self.assertEqual(result["r0_r12"]["r4"], "0x1000")
        self.assertEqual(result["stack_prefix_0x80"], bytes(range(0x80)).hex())
        self.assertEqual(result["pc_bytes_0x10"], (bytes.fromhex("0000a0e31e80bde8") + bytes(8)).hex())

    def test_timeout_snapshot_reads_saved_r4_word_only_at_pinned_svc_return_site(self):
        rsp = ReadTrackingProgressRsp()
        rsp.registers[13] = 0x10002000
        rsp.registers[14] = trace.ATOMIC_RECHECK_PC
        rsp.registers[15] = trace.SVC_RETURN_PC
        rsp.put(0x10002000, struct.pack("<II", 0x10004000, 0x471B58) + bytes(0x78))
        rsp.put(0x10004000, struct.pack("<III", 0xFFFFFFFF, 0x12345678, 3))

        result = trace.timeout_guest_snapshot(rsp, b"T02thread:1;")

        self.assertEqual(result["saved_r4_address_at_svc_return"], "0x10004000")
        self.assertEqual(result["word_at_saved_r4_at_interrupt"], "0xffffffff")
        self.assertEqual(result["word_at_saved_r4_signed"], -1)
        self.assertEqual(result["raw_words_at_saved_r4"], {
            "offset_0x0": "0xffffffff",
            "offset_0x4": "0x12345678",
            "offset_0x8": "0x3",
        })
        self.assertEqual(
            [read for read in rsp.memory_reads if read[0] >= 0x10004000],
            [(0x10004000, 4), (0x10004004, 4), (0x10004008, 4)],
        )

    def test_timeout_snapshot_does_not_read_an_unrelated_saved_r4_word(self):
        rsp = ProgressRsp()
        rsp.registers[13] = 0x10002000
        rsp.registers[14] = trace.ATOMIC_RECHECK_PC
        rsp.registers[15] = 0x002A88A4
        rsp.put(0x10002000, struct.pack("<I", 0x10004000) + bytes(0x7C))

        result = trace.timeout_guest_snapshot(rsp, b"T02thread:1;")

        self.assertNotIn("saved_r4_address_at_svc_return", result)
        self.assertNotIn("word_at_saved_r4_at_interrupt", result)

    def test_boot_dispatch_epilogue_is_armed_once_only_for_context_word_12(self):
        self.assertTrue(trace.should_arm_boot_dispatch_epilogue(0x001C05C4, 12, False))
        self.assertFalse(trace.should_arm_boot_dispatch_epilogue(0x001C05C4, 11, False))
        self.assertFalse(trace.should_arm_boot_dispatch_epilogue(0x001C05AC, 12, False))
        self.assertFalse(trace.should_arm_boot_dispatch_epilogue(0x001C05C4, 12, True))

    def test_boot_dispatch_epilogue_snapshot_reads_saved_return_without_guessing_context_name(self):
        rsp = EpilogueRsp()

        result = trace.boot_dispatch_epilogue_snapshot(rsp, 5.25)

        self.assertEqual(result["label"], "native-dispatch-common-return-before-pop")
        self.assertEqual(result["context_pointer"], "0x10001000")
        self.assertEqual(result["context_word_plus_8"], 12)
        self.assertEqual(result["saved_r4_raw"], "0xdeadbeef")
        self.assertEqual(result["saved_pc_raw"], "0x103164")
        self.assertEqual(result["pre_pop_r0"], "0x10")
        self.assertEqual(result["elapsed_s"], 5.25)

    def test_sync_wait_return_snapshot_reads_only_the_raw_word_at_r4(self):
        rsp = ProgressRsp()
        rsp.registers[4] = 0x00100000
        rsp.registers[15] = trace.ASD_SYNC_WAIT_RETURN_PC
        rsp.put(0x00100000, struct.pack("<I", 0xFFFFFFFE))

        event = trace.sync_wait_return_snapshot(
            rsp, trace.ASD_SYNC_WAIT_RETURN_PC, 2.5
        )

        self.assertEqual(event["label"], "sync-wait-return-observation")
        self.assertEqual(event["pc"], "0x2c36dc")
        self.assertEqual(event["r4_indirect_word_raw"], "0xfffffffe")
        self.assertNotIn("lock", event)

    def test_atomic_retry_snapshot_records_raw_registers_and_indirect_word(self):
        rsp = ProgressRsp()
        rsp.registers[2] = 0xFFFFFFFE
        rsp.registers[4] = 0x00100000
        rsp.put(0x00100000, struct.pack("<I", 0xFFFFFFFE))

        event = trace.atomic_retry_snapshot(
            rsp, trace.ATOMIC_RETRY_BRANCH_PC, 1.25
        )

        self.assertEqual(event["phase"], "conditional-branch-target")
        self.assertEqual(event["pc"], "0x1465cc")
        self.assertEqual(event["r2_signed"], -2)
        self.assertEqual(event["r4_indirect_word_raw"], "0xfffffffe")
        self.assertNotIn("lock", event)

    def test_atomic_retry_branch_rearms_only_after_first_branch_and_callsite(self):
        self.assertTrue(trace.should_rearm_atomic_retry_branch(1, 1))
        self.assertFalse(trace.should_rearm_atomic_retry_branch(0, 0))
        self.assertFalse(trace.should_rearm_atomic_retry_branch(1, 0))
        self.assertFalse(trace.should_rearm_atomic_retry_branch(2, 1))
        self.assertFalse(trace.should_rearm_atomic_retry_branch(1, 2))

    def test_early_lock_observers_are_opt_in_and_disabled_by_default(self):
        self.assertEqual(trace.startup_lock_path_breakpoints(False), ())
        self.assertEqual(trace.startup_lock_path_breakpoints(True), (
            trace.ATOMIC_RETRY_BRANCH_PC,
            trace.ASD_SYNC_WAIT_RETURN_PC,
            trace.ASD_LOCK_OBJECT_CALL_PC,
        ))

    def test_native_command_progress_breakpoints_are_opt_in(self):
        self.assertEqual(trace.startup_progress_breakpoints(False), ())
        self.assertEqual(
            trace.startup_progress_breakpoints(True), tuple(trace.SCRIPT_PROGRESS)
        )

    def test_lock_thread_compare_snapshot_reads_only_three_raw_object_words(self):
        rsp = ReadTrackingProgressRsp()
        rsp.registers[0] = 0x1FF82000
        rsp.registers[4] = 0x00100000
        rsp.put(0x00100000, struct.pack("<III", 0xFFFFFFFE, 0x1FF82800, 1))

        event = trace.lock_thread_compare_snapshot(
            rsp, trace.ASD_LOCK_THREAD_COMPARE_PC, 0.75
        )

        self.assertEqual(event["label"], "lock-thread-compare-raw-observation")
        self.assertEqual(event["current_thread_token_raw"], "0x1ff82000")
        self.assertEqual(event["object_base_raw"], "0x100000")
        self.assertEqual(event["object_words_raw"], {
            "offset_0x0": "0xfffffffe",
            "offset_0x4": "0x1ff82800",
            "offset_0x8": "0x1",
        })
        self.assertEqual(
            [read for read in rsp.memory_reads if read[0] >= 0x00100000],
            [(0x00100000, 12)],
        )

    def test_lock_thread_compare_filter_does_not_read_a_different_object(self):
        rsp = ReadTrackingProgressRsp()
        rsp.registers[0] = 0x1FF82000
        rsp.registers[4] = 0x00100000
        rsp.put(0x00100000, struct.pack("<III", 1, 2, 3))

        event = trace.lock_thread_compare_snapshot(
            rsp, trace.ASD_LOCK_THREAD_COMPARE_PC, 0.75, 0x00100004
        )

        self.assertFalse(event["target_base_match"])
        self.assertIsNone(event["object_words_raw"])
        self.assertEqual(
            [read for read in rsp.memory_reads if read[0] >= 0x00100000], []
        )

    def test_lock_object_return_snapshot_reads_three_words_and_one_raw_byte(self):
        rsp = ReadTrackingProgressRsp()
        rsp.registers[4] = 0x00100000
        rsp.put(0x00100000, struct.pack("<III", 0xFFFFFFFE, 0x1FF82800, 1))
        rsp.put(0x00100076, b"\x02")

        event = trace.lock_object_return_snapshot(
            rsp, trace.ASD_LOCK_OBJECT_RETURN_PC, 0.875, 0x00100000
        )

        self.assertEqual(event["label"], "lock-object-return-raw-observation")
        self.assertEqual(event["object_base_raw"], "0x100000")
        self.assertTrue(event["target_base_match"])
        self.assertEqual(event["object_words_raw"], {
            "offset_0x0": "0xfffffffe",
            "offset_0x4": "0x1ff82800",
            "offset_0x8": "0x1",
        })
        self.assertEqual(event["object_byte_0x76_raw"], "0x2")
        self.assertEqual(
            [read for read in rsp.memory_reads if read[0] >= 0x00100000],
            [(0x00100000, 12), (0x00100076, 1)],
        )

    def test_lock_object_return_snapshot_does_not_read_a_different_base(self):
        rsp = ReadTrackingProgressRsp()
        rsp.registers[4] = 0x00100000

        event = trace.lock_object_return_snapshot(
            rsp, trace.ASD_LOCK_OBJECT_RETURN_PC, 0.875, 0x00100004
        )

        self.assertFalse(event["target_base_match"])
        self.assertIsNone(event["object_words_raw"])
        self.assertIsNone(event["object_byte_0x76_raw"])
        self.assertEqual(
            [read for read in rsp.memory_reads if read[0] >= 0x00100000], []
        )

    def test_lock_object_return_snapshot_bounds_both_raw_reads(self):
        rsp = ReadTrackingProgressRsp()
        rsp.registers[4] = 0x1FFFFFF8

        event = trace.lock_object_return_snapshot(
            rsp, trace.ASD_LOCK_OBJECT_RETURN_PC, 0.875, 0x1FFFFFF8
        )

        self.assertIsNone(event["object_words_raw"])
        self.assertIsNone(event["object_byte_0x76_raw"])
        self.assertEqual(rsp.memory_reads, [])

    def test_lock_owner_store_snapshot_captures_prewrite_register_and_header(self):
        rsp = ReadTrackingProgressRsp()
        rsp.registers[0] = 0x1FF82000
        rsp.registers[4] = 0x00100000
        rsp.put(0x00100000, struct.pack("<III", 0xFFFFFFFE, 0, 0))

        event = trace.lock_owner_store_snapshot(
            rsp, trace.ASD_LOCK_OWNER_STORE_PC, 0.812, 0x00100000
        )

        self.assertEqual(event["label"], "lock-owner-store-prewrite-raw-observation")
        self.assertEqual(event["owner_value_raw"], "0x1ff82000")
        self.assertEqual(event["object_base_raw"], "0x100000")
        self.assertTrue(event["target_base_match"])
        self.assertEqual(event["object_words_raw"], {
            "offset_0x0": "0xfffffffe",
            "offset_0x4": "0x0",
            "offset_0x8": "0x0",
        })
        self.assertEqual(
            [read for read in rsp.memory_reads if read[0] >= 0x00100000],
            [(0x00100000, 12)],
        )

    def test_lock_owner_store_snapshot_filters_other_object_without_reads(self):
        rsp = ReadTrackingProgressRsp()
        rsp.registers[0] = 0x1FF82000
        rsp.registers[4] = 0x00100000

        event = trace.lock_owner_store_snapshot(
            rsp, trace.ASD_LOCK_OWNER_STORE_PC, 0.812, 0x00100004
        )

        self.assertFalse(event["target_base_match"])
        self.assertIsNone(event["object_words_raw"])
        self.assertEqual(
            [read for read in rsp.memory_reads if read[0] >= 0x00100000], []
        )

    def test_lock_owner_poststore_snapshot_reads_header_after_store_instruction(self):
        rsp = ReadTrackingProgressRsp()
        rsp.registers[0] = 0x1FF82800
        rsp.registers[4] = 0x00100000
        rsp.put(0x00100000, struct.pack("<III", 0xFFFFFFFF, 0x1FF82800, 0))

        event = trace.lock_owner_poststore_snapshot(
            rsp, trace.ASD_LOCK_OWNER_POSTSTORE_PC, 0.813, 0x00100000
        )

        self.assertEqual(event["label"], "lock-owner-poststore-raw-observation")
        self.assertEqual(event["r0_raw"], "0x1ff82800")
        self.assertEqual(event["object_words_raw"], {
            "offset_0x0": "0xffffffff",
            "offset_0x4": "0x1ff82800",
            "offset_0x8": "0x0",
        })
        self.assertEqual(
            [read for read in rsp.memory_reads if read[0] >= 0x00100000],
            [(0x00100000, 12)],
        )

    def test_lock_owner_poststore_snapshot_filters_mismatched_base(self):
        rsp = ReadTrackingProgressRsp()
        rsp.registers[0] = 0x1FF82800
        rsp.registers[4] = 0x00100000

        event = trace.lock_owner_poststore_snapshot(
            rsp, trace.ASD_LOCK_OWNER_POSTSTORE_PC, 0.813, 0x00100004
        )

        self.assertFalse(event["target_base_match"])
        self.assertIsNone(event["object_words_raw"])
        self.assertEqual(
            [read for read in rsp.memory_reads if read[0] >= 0x00100000], []
        )

    def test_targeted_caller_return_is_armed_only_for_the_observed_saved_pc(self):
        self.assertTrue(trace.should_arm_targeted_caller_return("0x103164"))
        self.assertFalse(trace.should_arm_targeted_caller_return(None))
        self.assertFalse(trace.should_arm_targeted_caller_return("0x103168"))

    def test_targeted_dispatch_return_executes_one_caller_instruction_without_rearm(self):
        rsp = ReturnStepRsp()
        active = {trace.DISPATCH_CALLER_RETURN}
        deadline = __import__("time").monotonic() + 2.0

        step_pc = trace.step_dispatch_caller_return(rsp, active, deadline)

        self.assertEqual(step_pc, "0x103168")
        self.assertEqual(
            rsp.breakpoints_at_continue,
            {trace.DISPATCH_CALLER_NEXT},
            "the stopped caller return must be unpatched while its instruction executes",
        )
        self.assertEqual(active, set())
        self.assertEqual(rsp.breakpoints, set())


    def test_targeted_caller_byte_probe_records_preloaded_mock_registers_at_one_stop(self):
        rsp = BranchInputRsp()
        active = set()
        started = __import__("time").monotonic() - 0.5

        event = trace.step_dispatch_caller_branch_input(
            rsp, active, __import__("time").monotonic() + 2.0, started
        )

        self.assertEqual(event["label"], "native-command-caller-branch-input")
        self.assertEqual(event["phase"], "after-original-ldrb-before-cmp")
        self.assertEqual(event["pc"], "0x10316c")
        self.assertEqual(event["r0_loaded_raw"], "0x1")
        self.assertEqual(event["r8_base_raw"], "0x14657380")
        self.assertEqual(event["source_address"], "0x14657390")
        self.assertEqual(rsp.breakpoints_at_continue, {trace.DISPATCH_CALLER_BRANCH_INPUT})
        self.assertEqual(active, set())
        self.assertEqual(rsp.breakpoints, set())

    def test_dispatch_caller_probe_requires_pinned_arm_words(self):
        image = bytearray(0x4000)
        for pc, word in trace.DISPATCH_CALLER_PROBE_ARM_WORDS.items():
            struct.pack_into("<I", image, pc - 0x00100000, word)
        observed = trace.verify_dispatch_caller_probe_arm_words(image)
        self.assertEqual(observed, {hex(pc): hex(word) for pc, word in trace.DISPATCH_CALLER_PROBE_ARM_WORDS.items()})
        struct.pack_into("<I", image, trace.DISPATCH_CALLER_BRANCH_INPUT - 0x00100000, 0)
        with self.assertRaises(trace.TraceError):
            trace.verify_dispatch_caller_probe_arm_words(image)

    def test_zero_path_mock_records_programmed_target_and_helper_return_stops(self):
        rsp = ZeroBranchPathRsp()
        active = set()
        started = __import__("time").monotonic() - 0.5

        events = trace.step_dispatch_caller_zero_path(
            rsp, active, __import__("time").monotonic() + 2.0, started
        )

        self.assertEqual([event["pc"] for event in events], ["0x10319c", "0x1031a4"])
        self.assertEqual(events[0]["label"], "native-command-caller-zero-branch-target")
        self.assertEqual(events[0]["r0_raw"], "0x0")
        self.assertEqual(events[1]["label"], "native-command-caller-common-helper-return")
        self.assertEqual(events[1]["r0_raw"], "0x1234")
        self.assertEqual(rsp.breakpoints_at_continue_history, [
            {trace.DISPATCH_CALLER_ZERO_BRANCH_TARGET},
            {trace.DISPATCH_CALLER_COMMON_HELPER_RETURN},
        ])
        self.assertEqual(active, set())
        self.assertEqual(rsp.breakpoints, set())

    def test_zero_path_probe_refuses_nonzero_loaded_byte_without_arming(self):
        rsp = ZeroBranchPathRsp()
        rsp.registers[0] = 1
        active = set()

        with self.assertRaises(trace.TraceError):
            trace.step_dispatch_caller_zero_path(
                rsp, active, __import__("time").monotonic() + 2.0, __import__("time").monotonic()
            )

        self.assertEqual(active, set())
        self.assertEqual(rsp.breakpoints, set())

if __name__ == "__main__":
    unittest.main()
