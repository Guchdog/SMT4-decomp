from __future__ import annotations

import socket
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from tools import h2_apt_utility4_caller_probe as probe


class FakeSocket:
    def __init__(self):
        self.timeouts = []
        self.sent = []
        self.closed = False

    def settimeout(self, value):
        self.timeouts.append(value)

    def sendall(self, value):
        self.sent.append(value)

    def close(self):
        self.closed = True


class FakeRsp:
    def __init__(self, *, max_hits=5, bad_register=None, break_insert=b"OK", stop_pc=None,
                 timeout_on_continue=False):
        self.sock = FakeSocket()
        self.timeout = 1.0
        self.max_hits = max_hits
        self.bad_register = bad_register
        self.break_insert = break_insert
        self.stop_pc = probe.BREAKPOINT if stop_pc is None else stop_pc
        self.timeout_on_continue = timeout_on_continue
        self.continues = 0
        self.packets = []
        self.breakpoint_clears = 0
        self.detaches = 0

    def request(self, payload, expected=None):
        self.packets.append(payload)
        if payload.startswith(b"qSupported"):
            reply = b"multiprocess+;swbreak+"
        elif payload == b"!":
            reply = b"OK"
        elif payload == b"qfProcessInfo":
            reply = b"pid:1234;endian:little;"
        elif payload.startswith(b"vAttach;"):
            reply = b"T05thread:1234;"
        elif payload.startswith(b"Z0,"):
            reply = self.break_insert
        elif payload.startswith(b"z0,"):
            self.breakpoint_clears += 1
            reply = b"OK"
        elif payload == b"D":
            self.detaches += 1
            reply = b"OK"
        elif payload[:1] == b"p":
            index = int(payload[1:], 16)
            if index == self.bad_register:
                reply = b"E01"
            else:
                value = self.stop_pc if index == 15 else (0x00102188 if index == 14 else index)
                reply = value.to_bytes(4, "little").hex().encode("ascii")
        else:
            raise AssertionError(f"unexpected RSP packet: {payload!r}")
        if expected is not None and reply != expected:
            raise probe.ProbeError(f"unexpected reply {reply!r}")
        return reply

    def continue_to_stop(self):
        self.continues += 1
        self.sock.sent.append(b"continue")
        if self.timeout_on_continue:
            raise socket.timeout("test timeout")
        return b"T05swbreak:;"

    def _packet(self):
        return b"T02thread:1234;"


class AddressAndStaticContractTests(unittest.TestCase):
    def test_lr_classification_distinguishes_two_direct_callers(self):
        first = probe.classify_lr(0x00102188)
        second = probe.classify_lr(0x001051E0)
        indirect = probe.classify_lr(0x00103188)
        self.assertEqual(first["classification"], "known_direct_caller")
        self.assertEqual(first["caller_callsite"], "0x00102184")
        self.assertEqual(second["caller_callsite"], "0x001051dc")
        self.assertEqual(indirect["classification"], "unexpected_or_indirect")
        self.assertIsNone(indirect["caller_callsite"])

    def test_runtime_code_input_resolves_inside_semantic_checkout(self):
        root = probe.ROOT.resolve(strict=True)
        code_path = (root / probe.CODE_REL).resolve(strict=True)
        self.assertTrue(code_path.is_relative_to(root))
        self.assertEqual(probe.sha256(code_path), probe.CODE_SHA256)

    def test_static_pinned_code_and_preserved_log_counts(self):
        root = probe.ROOT
        evidence = probe.static_contract(root / probe.CODE_REL,
                                         root / probe.RUN017_LOG_REL,
                                         root / probe.RUN028_LOG_REL)
        self.assertEqual(evidence["helper_command_word"], "0xe3a00004")
        self.assertEqual(evidence["wrapper_call_target"], "0x002b5a1c")
        self.assertEqual(evidence["direct_arm_bl_callers"], ["0x00102184", "0x001051dc"])
        self.assertEqual([row["utility4_line_count"] for row in evidence["historical_utility4_logs"]], [4, 6452])

    def test_max_hit_control_rejects_more_than_four(self):
        for invalid in (0, 5, -1):
            with self.subTest(invalid=invalid), self.assertRaises(probe.ProbeError):
                probe.validate_max_hits(invalid)

    def test_runtime_task_uses_its_packet_root_for_reports_and_staging(self):
        packet = Path("build/agent-work/H2-semantic/h2-apt-utility4-caller-probe-runtime/run-001")
        self.assertEqual(
            probe.derive_output_root(probe.RUNTIME_TASK_ID, packet), packet.resolve()
        )

    def test_implementation_task_keeps_runtime_artifacts_in_its_packet_child(self):
        packet = Path("build/agent-work/H2-semantic/h2-apt-utility4-caller-probe/run-002")
        self.assertEqual(
            probe.derive_output_root(probe.TASK_ID, packet), (packet / "runtime-captures").resolve()
        )

    def test_output_root_cannot_escape_selected_packet(self):
        packet = Path("build/agent-work/H2-semantic/h2-apt-utility4-caller-probe-runtime/run-001")
        with self.assertRaisesRegex(probe.ProbeError, "inside the selected task"):
            probe.derive_output_root(probe.RUNTIME_TASK_ID, packet, Path("build/outside"))

    def test_listener_parser_records_exact_loopback_row_and_pid(self):
        text = ("Proto Local Address Foreign Address State PID\n"
                "TCP 127.0.0.1:46797 0.0.0.0:0 LISTENING 4321\n")
        binding = probe.parse_listener_binding(text, 46797)
        self.assertEqual(binding["local_address"], "127.0.0.1")
        self.assertEqual(binding["pid"], 4321)
        self.assertEqual(binding["netstat_row"], "TCP 127.0.0.1:46797 0.0.0.0:0 LISTENING 4321")

    def test_listener_parser_rejects_non_loopback_and_ambiguous_rows(self):
        wide = ("Proto Local Address Foreign Address State PID\n"
                "TCP 0.0.0.0:46797 0.0.0.0:0 LISTENING 4321\n")
        with self.assertRaisesRegex(probe.ProbeError, "exactly 127.0.0.1"):
            probe.parse_listener_binding(wide, 46797)
        duplicate = ("Proto Local Address Foreign Address State PID\n"
                     "TCP 127.0.0.1:46797 0.0.0.0:0 LISTENING 4321\n"
                     "TCP 127.0.0.1:46797 0.0.0.0:0 LISTENING 4322\n")
        with self.assertRaisesRegex(probe.ProbeError, "expected one listener row"):
            probe.parse_listener_binding(duplicate, 46797)

    def test_runtime_gate_attestation_requires_four_hashed_passes(self):
        with tempfile.TemporaryDirectory() as temp:
            packet = Path(temp) / "runtime-task"
            checks = packet / "checks"
            checks.mkdir(parents=True)
            gates = {}
            for name in probe.REQUIRED_OFFLINE_GATES:
                report = checks / f"{name}.json"
                report.write_text(json.dumps({"status": "passed", "gate": name}), encoding="utf-8")
                gates[name] = {"status": "passed", "report_path": str(report),
                               "sha256": hashlib.sha256(report.read_bytes()).hexdigest(),
                               "result_counts": {"cases_passed": 3},
                               "source_identity_warnings": ([{"source": "example", "matches": False}]
                                                             if name == "h2_differential" else [])}
                if name == "arm_thumb_interworking":
                    gates[name]["interworking_fields"] = {
                        "checked_original_bl_targets": {"0x1ea348": "0x30a9a4"},
                        "checked_lock_return_site": {"pc": "0x0"},
                        "checked_lock_owner_store_site": {"pc": "0x4"},
                        "checked_lock_owner_poststore_site": {"pc": "0x8"},
                        "checked_dispatch_caller_byte_probe_instructions": ["0xe1a00000"],
                    }
            attestation_path = packet / "offline-gate-attestation.json"
            attestation_path.write_text("{}", encoding="utf-8")
            document = {"schema_version": 1, "task_id": probe.RUNTIME_TASK_ID, "gates": gates}
            result = probe.validate_gate_attestation_document(document, attestation_path, packet)
            self.assertEqual(len(result["gates"]), 4)
            self.assertEqual({item["status"] for item in result["gates"]}, {"passed"})
            self.assertEqual(result["source_identity_warning_count"], 1)
            self.assertEqual(result["status_summary"], "passed_with_warnings")
            arm = next(item for item in result["gates"] if item["name"] == "arm_thumb_interworking")
            self.assertEqual(set(arm["interworking_fields"]), set(probe.REQUIRED_INTERWORKING_FIELDS))

    def test_runtime_gate_attestation_rejects_failed_or_changed_report(self):
        with tempfile.TemporaryDirectory() as temp:
            packet = Path(temp) / "runtime-task"
            checks = packet / "checks"
            checks.mkdir(parents=True)
            gates = {}
            for name in probe.REQUIRED_OFFLINE_GATES:
                report = checks / f"{name}.json"
                report.write_text("{}", encoding="utf-8")
                gates[name] = {"status": "passed", "report_path": str(report),
                               "sha256": hashlib.sha256(report.read_bytes()).hexdigest(),
                               "result_counts": {"cases_passed": 1},
                               "source_identity_warnings": []}
                if name == "arm_thumb_interworking":
                    gates[name]["interworking_fields"] = {key: {} for key in probe.REQUIRED_INTERWORKING_FIELDS}
            attestation = packet / "attestation.json"
            attestation.write_text("{}", encoding="utf-8")
            document = {"schema_version": 1, "task_id": probe.RUNTIME_TASK_ID, "gates": gates}
            gates[probe.REQUIRED_OFFLINE_GATES[0]]["sha256"] = "0" * 64
            with self.assertRaisesRegex(probe.ProbeError, "hash mismatch"):
                probe.validate_gate_attestation_document(document, attestation, packet)
            gates[probe.REQUIRED_OFFLINE_GATES[0]]["sha256"] = hashlib.sha256(
                (checks / f"{probe.REQUIRED_OFFLINE_GATES[0]}.json").read_bytes()).hexdigest()
            gates[probe.REQUIRED_OFFLINE_GATES[1]]["status"] = "failed"
            with self.assertRaisesRegex(probe.ProbeError, "did not pass"):
                probe.validate_gate_attestation_document(document, attestation, packet)


class RuntimeDependencyStagingTests(unittest.TestCase):
    def _write_pin(self, root: Path, rows: list[tuple[str, bytes]]) -> Path:
        root.mkdir(parents=True, exist_ok=True)
        files=[]
        for relative, payload in rows:
            path=root.joinpath(*relative.split("/"))
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(payload)
            files.append({"path":relative,"bytes":len(payload),
                          "sha256":hashlib.sha256(payload).hexdigest()})
        manifest=root.parent/"runtime-pin.json"
        manifest.write_text(json.dumps({"schema_version":1,"source_root":str(root),
                                        "runtime_files":files,
                                        "runtime_file_count":len(files)},indent=2),
                            encoding="utf-8")
        return manifest

    def test_manifest_pins_and_stages_only_exact_assets(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/"source"
            manifest=self._write_pin(root,[("Qt6Core.dll",b"qt-core"),
                                           ("plugins/platforms/qwindows.dll",b"qwindows")])
            (root/"unlisted.bin").write_bytes(b"must not copy")
            pin=probe.verify_runtime_dependency_manifest(manifest)
            app=Path(temp)/"stage"/"app"
            app.mkdir(parents=True)
            staged=probe.copy_pinned_runtime_dependencies(pin,app)
            self.assertEqual(pin["asset_count"],2)
            self.assertEqual(len(staged),2)
            self.assertEqual(
                sorted(path.relative_to(app).as_posix() for path in app.rglob("*") if path.is_file()),
                ["Qt6Core.dll","plugins/platforms/qwindows.dll"],
            )
            self.assertTrue(all(row["source_unchanged_after_copy"] for row in staged))
            self.assertTrue(probe.verify_runtime_dependency_sources(pin)["unchanged"])
            (root/"Qt6Core.dll").write_bytes(b"changed after staging")
            self.assertFalse(probe.verify_runtime_dependency_sources(pin)["unchanged"])

    def test_manifest_fails_closed_on_missing_mismatch_unsafe_and_duplicate_paths(self):
        with tempfile.TemporaryDirectory() as temp:
            base=Path(temp)
            root=base/"source"
            root.mkdir()
            (root/"one.dll").write_bytes(b"one")
            good=hashlib.sha256(b"one").hexdigest()
            cases=[
                ("missing", [{"path":"missing.dll","bytes":1,"sha256":good}],
                 "is missing"),
                ("hash", [{"path":"one.dll","bytes":3,"sha256":"0"*64}],
                 "hash/size mismatch"),
                ("unsafe", [{"path":"../escape.dll","bytes":1,"sha256":good}],
                 "unsafe runtime dependency path"),
                ("duplicate", [{"path":"one.dll","bytes":3,"sha256":good},
                               {"path":"ONE.DLL","bytes":3,"sha256":good}],
                 "duplicate"),
            ]
            for name, rows, message in cases:
                with self.subTest(name=name):
                    manifest=base/f"{name}.json"
                    manifest.write_text(json.dumps({
                        "schema_version":1,"source_root":str(root),
                        "runtime_files":rows,"runtime_file_count":len(rows),
                    }),encoding="utf-8")
                    with self.assertRaisesRegex(probe.ProbeError,message):
                        probe.verify_runtime_dependency_manifest(manifest)

    def test_stage_runtime_refuses_unpinned_dependencies(self):
        with tempfile.TemporaryDirectory() as temp:
            stage=Path(temp)/"stage"
            stage.mkdir()
            with self.assertRaisesRegex(probe.ProbeError,"verified dependency manifest"):
                probe.stage_runtime(Path("unused.exe"),Path("unused.cci"),Path("seed"),
                                    Path("fixture.sav"),stage,None)
            self.assertEqual(list(stage.iterdir()),[])

    def test_execute_refuses_unpinned_task_before_staging_or_launch(self):
        info={"task":{"task":{"id":probe.TASK_ID}},"runtime_dependencies":None}
        with patch.object(probe,"validate_task_and_inputs",return_value=info):
            with self.assertRaisesRegex(probe.ProbeError,"verified runtime dependency manifest"):
                probe.execute(SimpleNamespace(),{})
    
    def test_staging_rechecks_source_before_copy(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/"source"
            manifest=self._write_pin(root,[("Qt6Core.dll",b"pinned")])
            pin=probe.verify_runtime_dependency_manifest(manifest)
            (root/"Qt6Core.dll").write_bytes(b"changed")
            app=Path(temp)/"stage"/"app"
            app.mkdir(parents=True)
            with self.assertRaisesRegex(probe.ProbeError,"changed before staging"):
                probe.copy_pinned_runtime_dependencies(pin,app)
            self.assertEqual(list(app.rglob("*")),[])



class RuntimeLaunchPathTests(unittest.TestCase):
    def test_command_requires_exact_verified_executable_port_and_game(self):
        executable = Path("C:/isolated/app/azahar.exe")
        game = Path("C:/isolated/pinned.cci")
        command = [str(executable), "-g", "61582", str(game)]
        probe.validate_launch_command(command, executable, 61582, game)
        for index, wrong in ((0, "other.exe"), (1, "--other"), (2, "1234"), (3, "other.cci")):
            changed = command.copy()
            changed[index] = wrong
            with self.assertRaisesRegex(probe.ProbeError, "child command"):
                probe.validate_launch_command(changed, executable, 61582, game)
        with self.assertRaisesRegex(probe.ProbeError, "child command"):
            probe.validate_launch_command(command + ["extra"], executable, 61582, game)

    def test_windows_alias_identifies_existing_file(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "long staged executable.exe"
            target.write_bytes(b"owned staged executable")
            alias = probe.windows_short_path(target)
            self.assertTrue(probe.os.path.samefile(target, alias))

    def test_rejects_alias_that_still_produces_long_save_path(self):
        staged = {"executable": Path("C:/" + "x" * 130 + "/app/azahar.exe"),
                  "game": Path("C:/game.cci")}
        with patch.object(probe, "windows_short_path", side_effect=lambda p: p):
            with self.assertRaisesRegex(probe.ProbeError, "still too long"):
                probe.runtime_launch_paths(staged)

    def test_log_evidence_requires_isolated_profile_and_expected_title(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            app = root / "app"
            user = app / "user"
            (user / "log").mkdir(parents=True)
            exe = app / "azahar.exe"
            game = root / "game.cci"
            exe.write_bytes(b"exe")
            game.write_bytes(b"game")
            log = user / "log" / "azahar_log.txt"
            staged = {"user_dir": user, "game": game}
            log.write_text(f"{user}/nand/file\nProgram ID: 00040000000E5C00\n", encoding="utf-8")
            evidence = probe.staged_alias_log_evidence(staged, exe, game)
            self.assertTrue(evidence["profile_path_in_log"])
            self.assertTrue(evidence["title_id_in_log"])
            self.assertEqual(evidence["cci_filename_log_check"], "not_used")
            log.write_text(f"{user}/nand/file\nProgram ID: 0004000000000000\n", encoding="utf-8")
            self.assertFalse(probe.staged_alias_log_evidence(staged, exe, game)["title_id_in_log"])
            log.write_text("C:/other/user/nand/file\nProgram ID: 00040000000E5C00\n", encoding="utf-8")
            self.assertFalse(probe.staged_alias_log_evidence(staged, exe, game)["profile_path_in_log"])
            other = root / "other.cci"
            other.write_bytes(b"other")
            with self.assertRaisesRegex(probe.ProbeError, "no longer identify"):
                probe.staged_alias_log_evidence(staged, exe, other)


class DiagnosticLogPreservationTests(unittest.TestCase):
    def test_preserves_only_staged_log_with_digest(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            user = root / "user"
            output = root / "output"
            (user / "log").mkdir(parents=True)
            output.mkdir()
            log = user / "log" / "azahar_log.txt"
            log.write_bytes(b"diagnostic log\n")
            save = user / "save.sav"
            save.write_bytes(b"fixture")
            with patch.object(probe, "sha256", side_effect=AssertionError("unbounded hash used")):
                result = probe.preserve_staged_azahar_log(user, output, "stage-" + "a" * 32)
            self.assertEqual(result["status"], "preserved")
            self.assertEqual(Path(result["path"]).read_bytes(), log.read_bytes())
            self.assertEqual(result["sha256"], probe.sha256(log))
            self.assertEqual(save.read_bytes(), b"fixture")
            self.assertEqual(len(list(output.iterdir())), 1)

    def test_missing_log_and_unsafe_name_fail_safely(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            user = root / "user"
            output = root / "output"
            user.mkdir()
            output.mkdir()
            self.assertEqual(probe.preserve_staged_azahar_log(user, output, "stage-" + "b" * 32),
                             {"status": "absent"})
            with self.assertRaisesRegex(probe.ProbeError, "invalid stage name"):
                probe.preserve_staged_azahar_log(user, output, "../escape")
            self.assertEqual(list(output.iterdir()), [])

    def test_rejects_oversized_log_without_copy(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            user = root / "user"
            output = root / "output"
            (user / "log").mkdir(parents=True)
            output.mkdir()
            (user / "log" / "azahar_log.txt").write_bytes(b"x" * (8 * 1024 * 1024 + 1))
            with self.assertRaisesRegex(probe.ProbeError, "exceeds"):
                probe.preserve_staged_azahar_log(user, output, "stage-" + "c" * 32)
            self.assertEqual(list(output.iterdir()), [])


class RuntimeCompatibilityTests(unittest.TestCase):
    def _fixture(self, root):
        executable = root / probe.AZAHAR_COMPAT_EXECUTABLE_REL
        executable.parent.mkdir(parents=True, exist_ok=True)
        executable.write_bytes(b"known-good private loopback executable")
        prior_run = root / probe.AZAHAR_COMPAT_PRIOR_RUN_REL
        prior_run.parent.mkdir(parents=True, exist_ok=True)
        prior_run.write_text(json.dumps({
            "passed": True,
            "private_azahar_sha256": probe.sha256(executable),
        }), encoding="utf-8")
        pin_path = root / probe.AZAHAR_RUNTIME_PACKAGE_PIN_REL
        pin_path.parent.mkdir(parents=True, exist_ok=True)
        pin_path.write_text(json.dumps({
            "compatibility_evidence": {
                "private_executable": probe.AZAHAR_COMPAT_EXECUTABLE_REL,
                "private_executable_sha256": probe.sha256(executable),
                "successful_prior_run": probe.AZAHAR_COMPAT_PRIOR_RUN_REL,
                "successful_prior_run_sha256": probe.sha256(prior_run),
            },
        }), encoding="utf-8")
        packet_inputs = {
            probe.AZAHAR_RUNTIME_PACKAGE_PIN_REL.as_posix(): {"sha256": probe.sha256(pin_path)},
            probe.AZAHAR_COMPAT_EXECUTABLE_REL: {"sha256": probe.sha256(executable)},
            probe.AZAHAR_COMPAT_PRIOR_RUN_REL: {"sha256": probe.sha256(prior_run)},
        }
        return executable, pin_path, prior_run, packet_inputs

    def test_runtime_compatibility_requires_pinned_prior_success_and_binary(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            executable, _, _, packet_inputs = self._fixture(root)
            with patch.object(probe, "ROOT", root):
                record = {}
                result = probe.validate_runtime_compatibility_executable(
                    executable, packet_inputs, record)
            self.assertTrue(result["matches_compatibility_hash"])
            self.assertTrue(result["successful_prior_run_passed"])
            self.assertEqual(record["private_azahar"]["sha256"], probe.sha256(executable))
            self.assertEqual(record["private_azahar"]["observed_binary_sha256"], probe.sha256(executable))

    def test_runtime_compatibility_rejects_changed_executable(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            executable, _, _, packet_inputs = self._fixture(root)
            executable.write_bytes(b"different executable")
            with patch.object(probe, "ROOT", root):
                with self.assertRaisesRegex(probe.ProbeError, "compatibility hash"):
                    probe.validate_runtime_compatibility_executable(
                        executable, packet_inputs, {})

    def test_runtime_compatibility_rejects_failed_prior_run(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            executable, pin_path, prior_run, packet_inputs = self._fixture(root)
            prior_run.write_text(json.dumps({
                "passed": False,
                "private_azahar_sha256": probe.sha256(executable),
            }), encoding="utf-8")
            pin = json.loads(pin_path.read_text(encoding="utf-8"))
            pin["compatibility_evidence"]["successful_prior_run_sha256"] = probe.sha256(prior_run)
            pin_path.write_text(json.dumps(pin), encoding="utf-8")
            packet_inputs[probe.AZAHAR_RUNTIME_PACKAGE_PIN_REL.as_posix()]["sha256"] = probe.sha256(pin_path)
            packet_inputs[probe.AZAHAR_COMPAT_PRIOR_RUN_REL]["sha256"] = probe.sha256(prior_run)
            with patch.object(probe, "ROOT", root):
                with self.assertRaisesRegex(probe.ProbeError, "does not prove a prior successful run"):
                    probe.validate_runtime_compatibility_executable(
                        executable, packet_inputs, {})

    def test_runtime_compatibility_rejects_packet_hash_mismatch(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            executable, _, _, packet_inputs = self._fixture(root)
            packet_inputs[probe.AZAHAR_COMPAT_EXECUTABLE_REL]["sha256"] = "0" * 64
            with patch.object(probe, "ROOT", root):
                with self.assertRaisesRegex(probe.ProbeError, "not pinned by the task packet"):
                    probe.validate_runtime_compatibility_executable(
                        executable, packet_inputs, {})


class PacketAndDeadlineTests(unittest.TestCase):
    def test_every_packet_input_hash_is_recomputed_and_mismatch_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            seed = root / "build" / "profile"
            seed.mkdir(parents=True)
            mac = seed / "mac.txt"
            mac.write_bytes(b"disposable mac seed")
            rel = "build/profile/mac.txt"
            digest = hashlib.sha256(mac.read_bytes()).hexdigest()
            packet = {"input_sha256": {rel: digest}}
            evidence = probe.verify_packet_inputs(packet, root, (rel,))
            self.assertEqual(evidence[rel]["sha256"], digest)
            mac.write_bytes(b"changed")
            with self.assertRaisesRegex(probe.ProbeError, "SHA-256 mismatch"):
                probe.verify_packet_inputs(packet, root, (rel,))

    def test_profile_seed_packet_pin_set_must_match_complete_live_tree(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            seed = root / "build" / "profile"
            seed.mkdir(parents=True)
            first, second = seed / "mac.txt", seed / "nand-config"
            first.write_bytes(b"mac")
            second.write_bytes(b"nand")
            paths = {"build/profile/mac.txt": first,
                     "build/profile/nand-config": second}
            packet = {"input_sha256": {
                name: hashlib.sha256(path.read_bytes()).hexdigest()
                for name, path in paths.items()}}
            pins = probe.verify_packet_inputs(packet, root)
            audit = probe.verify_profile_seed_manifest(seed, pins, root)
            self.assertEqual(audit["file_count"], 2)
            incomplete = dict(pins)
            incomplete.pop("build/profile/nand-config")
            with self.assertRaisesRegex(probe.ProbeError, "pin set differs"):
                probe.verify_profile_seed_manifest(seed, incomplete, root)

    def test_deadline_rsp_clamps_each_fragmented_receive_to_remaining_time(self):
        class RawSocket:
            def __init__(self):
                self.timeouts = []
                self.data = [b"a", b"b"]

            def settimeout(self, value):
                self.timeouts.append(value)

            def recv(self, _count):
                return self.data.pop(0)

            def sendall(self, _payload):
                pass

            def close(self):
                pass

        raw = RawSocket()
        rsp = probe.DeadlineRsp(raw, deadline=101.0, packet_timeout=5.0)
        with patch.object(probe.time, "monotonic", side_effect=[100.0, 100.75, 100.75, 100.75]):
            self.assertEqual(rsp._exact(2), b"ab")
        self.assertEqual(raw.timeouts, [1.0, 0.25])

    def test_deadline_rsp_rejects_io_after_absolute_deadline(self):
        raw = FakeSocket()
        rsp = probe.DeadlineRsp(raw, deadline=1.0, packet_timeout=5.0)
        with patch.object(probe.time, "monotonic", return_value=1.0):
            with self.assertRaises(probe.DeadlineExpired):
                rsp._exact(1)
        self.assertEqual(raw.timeouts, [])


class CaptureTests(unittest.TestCase):
    def test_collect_hits_stops_at_configured_bound_and_reads_registers(self):
        rsp = FakeRsp(max_hits=6)
        hits, stop = probe.collect_hits(rsp, 4, 5.0)
        self.assertEqual(len(hits), 4)
        self.assertEqual(stop, "max_hits_reached")
        self.assertEqual(rsp.continues, 4)
        self.assertEqual(hits[0]["pc"], "0x002c0ee0")
        self.assertEqual(hits[0]["lr"]["classification"], "known_direct_caller")
        self.assertEqual(set(hits[0]["registers"]), set(probe.REGISTER_NAMES))

    def test_capture_sets_and_clears_one_breakpoint_and_detaches(self):
        rsp = FakeRsp(max_hits=2)
        result = probe.capture_session(rsp, 2, 5.0)
        self.assertEqual(len(result["hits"]), 2)
        self.assertTrue(result["breakpoint_set"])
        self.assertTrue(result["breakpoint_cleared"])
        self.assertTrue(result["detached"])
        self.assertEqual(rsp.breakpoint_clears, 1)
        self.assertEqual(rsp.detaches, 1)
        verbs = [packet[:1] for packet in rsp.packets]
        self.assertNotIn(b"M", verbs)
        self.assertNotIn(b"P", verbs)
        self.assertNotIn(b"X", verbs)
        self.assertEqual(result["explicit_rsp_memory_write_packets"], [])
        self.assertEqual(result["software_breakpoint"]["insert_packet"], "Z0")
        self.assertEqual(result["software_breakpoint"]["remove_packet"], "z0")
        self.assertEqual(result["logical_inputs_injected"], 0)

    def test_rsp_breakpoint_error_detaches_without_clearing_unset_breakpoint(self):
        rsp = FakeRsp(break_insert=b"E01")
        with self.assertRaisesRegex(probe.ProbeError, "breakpoint was not accepted"):
            probe.capture_session(rsp, 4, 5.0)
        self.assertEqual(rsp.breakpoint_clears, 0)
        self.assertEqual(rsp.detaches, 1)
        self.assertTrue(rsp.sock.closed)

    def test_rsp_register_error_clears_breakpoint_and_detaches(self):
        rsp = FakeRsp(bad_register=14)
        with self.assertRaisesRegex(probe.ProbeError, "could not read r14"):
            probe.capture_session(rsp, 4, 5.0)
        self.assertEqual(rsp.breakpoint_clears, 1)
        self.assertEqual(rsp.detaches, 1)
        self.assertTrue(rsp.sock.closed)

    def test_unexpected_stop_pc_is_an_error_and_still_cleans_breakpoint(self):
        rsp = FakeRsp(stop_pc=0x001E989C)
        with self.assertRaisesRegex(probe.ProbeError, "expected 0x002c0ee0"):
            probe.capture_session(rsp, 4, 5.0)
        self.assertEqual(rsp.breakpoint_clears, 1)
        self.assertEqual(rsp.detaches, 1)

    def test_timeout_interrupts_continue_without_claiming_a_hit(self):
        rsp = FakeRsp(timeout_on_continue=True)
        hits, stop = probe.collect_hits(rsp, 4, 5.0)
        self.assertEqual(hits, [])
        self.assertEqual(stop, "capture_timeout")
        self.assertIn(b"\x03", rsp.sock.sent)


class CleanupTests(unittest.TestCase):
    def test_cleanup_removes_only_owned_staging_child(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "captures"
            root.mkdir()
            stage = root / "stage-test"
            stage.mkdir()
            (stage / "profile.bin").write_bytes(b"disposable")
            sibling = root / "keep-report.json"
            sibling.write_text("evidence", encoding="utf-8")
            self.assertTrue(probe.remove_owned_stage(root, stage))
            self.assertFalse(stage.exists())
            self.assertTrue(sibling.is_file())

    def test_cleanup_refuses_path_outside_owned_staging_root(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "captures"
            root.mkdir()
            outside = Path(temp) / "stage-outside"
            outside.mkdir()
            marker = outside / "keep"
            marker.write_text("preserve", encoding="utf-8")
            with self.assertRaisesRegex(probe.ProbeError, "outside the owned"):
                probe.remove_owned_stage(root, outside)
            self.assertTrue(marker.is_file())

    def test_process_cleanup_terminates_child(self):
        class Process:
            pid = 99
            returncode = None
            terminated = False

            def poll(self):
                return self.returncode

            def terminate(self):
                self.terminated = True

            def wait(self, timeout=None):
                self.returncode = 0
                return 0

        process = Process()
        result = probe.stop_child(process)
        self.assertTrue(process.terminated)
        self.assertEqual(result, {"terminated": True, "exit_code": 0})


class EndToEndTimeoutCleanupTests(unittest.TestCase):
    def test_timeout_flows_through_capture_and_execute_finalization(self):
        class Process:
            pid = 4321

            def __init__(self):
                self.returncode = None
                self.terminated = False

            def poll(self):
                return self.returncode

            def terminate(self):
                self.terminated = True
                self.returncode = 0

            def wait(self, timeout=None):
                self.returncode = 0
                return 0

            def kill(self):
                self.returncode = -9

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            output = root / "runtime-packet"
            output.mkdir()
            source_exe = root / "azahar.exe"
            source_game = root / "game.cci"
            fixture = root / "source-fixture.sav"
            seed = root / "profile-seed"
            seed.mkdir()
            (seed / "marker.bin").write_bytes(b"profile")
            source_exe.write_bytes(b"azahar")
            source_game.write_bytes(b"cci")
            fixture.write_bytes(b"disposable save")
            seed_manifest = probe.shared.file_manifest(seed)
            record = {
                "output_root": str(output),
                "private_azahar": {"observed_binary_sha256": probe.sha256(source_exe)},
                "inputs": {
                    "game_sha256": probe.sha256(source_game),
                    "disposable_save_fixture_sha256": probe.sha256(fixture),
                    "profile_seed_files": seed_manifest,
                },
            }
            runtime_asset = root / "pinned-runtime.dll"
            runtime_asset.write_bytes(b"pinned runtime dependency")
            info = {
                "task": {"task": {"id": probe.RUNTIME_TASK_ID}},
                "packet_root": output,
                "source_exe": source_exe,
                "game": source_game,
                "fixture": fixture,
                "profile_seed": seed,
                "runtime_dependencies": {
                    "source_root": str(root),
                    "assets": [{
                        "relative_path": "pinned-runtime.dll",
                        "source": str(runtime_asset),
                        "sha256": probe.sha256(runtime_asset),
                        "bytes": runtime_asset.stat().st_size,
                    }],
                },
            }
            args = SimpleNamespace(
                startup_timeout=0.2, capture_timeout=8.0, packet_timeout=0.5,
                port=38765, max_hits=4, output_root=None,
            )
            process = Process()
            stage_state = {}

            class FakeLoopbackRspSocket:
                def __init__(self):
                    self.timeouts = []
                    self.pending = bytearray()
                    self.closed = False
                    self.timeout_after_continue_ack = False
                    self.continue_timeouts = 0
                    self.interrupts = 0
                    self.commands = []

                def settimeout(self, value):
                    self.timeouts.append(value)

                def _queue_packet(self, payload):
                    self.pending.extend(b"+")
                    self.pending.extend(probe.shared.frame(payload))

                def sendall(self, payload):
                    if payload == b"+":
                        return
                    if payload == b"\x03":
                        self.interrupts += 1
                        self.pending.extend(probe.shared.frame(b"T02thread:1234;"))
                        return
                    command = probe.shared.parse_frame(payload)
                    self.commands.append(command)
                    if command == b"c":
                        self.pending.extend(b"+")
                        self.timeout_after_continue_ack = True
                        self.continue_timeouts += 1
                        stage_state["save"].write_bytes(b"mutated disposable copy")
                        return
                    if command.startswith(b"qSupported"):
                        reply = b"multiprocess+;swbreak+"
                    elif command == b"!":
                        reply = b"OK"
                    elif command == b"qfProcessInfo":
                        reply = b"pid:1234;endian:little;"
                    elif command == b"vAttach;1234":
                        reply = b"T05thread:1234;"
                    elif command == f"Z0,{probe.BREAKPOINT:x},4".encode("ascii"):
                        reply = b"OK"
                    elif command == f"z0,{probe.BREAKPOINT:x},4".encode("ascii"):
                        reply = b"OK"
                    elif command == b"D":
                        reply = b"OK"
                    else:
                        raise AssertionError(f"unexpected RSP command: {command!r}")
                    self._queue_packet(reply)

                def recv(self, count):
                    if self.pending:
                        result = bytes(self.pending[:count])
                        del self.pending[:count]
                        return result
                    if self.timeout_after_continue_ack:
                        self.timeout_after_continue_ack = False
                        raise socket.timeout("bounded fake continue timeout")
                    raise AssertionError("fake RSP peer received an unexpected read")

                def close(self):
                    self.closed = True

            def stage_runtime(_exe, game, _seed, save_fixture, stage_dir, _runtime_dependencies=None):
                app_dir = stage_dir / "app"
                app_dir.mkdir()
                user_dir = app_dir / "user"
                user_dir.mkdir()
                staged_exe = app_dir / "azahar.exe"
                staged_exe.write_bytes(source_exe.read_bytes())
                staged_game = stage_dir / "pinned-title.cci"
                staged_game.write_bytes(game.read_bytes())
                staged_save = user_dir / probe.SAVE_REL
                staged_save.parent.mkdir(parents=True)
                staged_save.write_bytes(save_fixture.read_bytes())
                stage_state["save"] = staged_save
                return {
                    "run_dir": str(stage_dir), "executable": staged_exe,
                    "game": staged_game, "app_dir": app_dir, "user_dir": user_dir,
                    "profile_files": [], "package_assets": [],
                    "runtime_files_before": probe.shared.file_manifest(
                        app_dir, excluded_top_level={"user"}),
                    "staged_save_path": staged_save,
                    "staged_save_sha256_before": probe.sha256(staged_save),
                }

            raw_socket = FakeLoopbackRspSocket()
            with (
                patch.object(probe, "validate_task_and_inputs", return_value=info),
                patch.object(probe.shared, "reserve_port"),
                patch.object(probe, "stage_runtime", side_effect=stage_runtime),
                patch.object(probe, "runtime_launch_paths", side_effect=lambda s: (s["executable"], s["game"], 100)),
                patch.object(probe.shared, "azahar_command", side_effect=lambda exe, port, game: [str(exe), "-g", str(port), str(game)]),
                patch.object(probe.subprocess, "Popen", return_value=process),
                patch.object(probe, "listener_binding", side_effect=[
                    {"local_address": "127.0.0.1", "local_port": 38765,
                     "pid": process.pid, "netstat_row": "test"}, None]),
                patch.object(probe, "staged_alias_log_evidence", return_value={"profile_path_in_log": True, "title_id_in_log": True}),
                patch.object(probe.socket, "create_connection", return_value=raw_socket),
            ):
                result = probe.execute(args, record)

            self.assertEqual(result["status"], "captured_partial")
            self.assertEqual(result["rsp"]["capture_stop"], "capture_timeout")
            self.assertTrue(result["rsp"]["breakpoint_set"])
            self.assertTrue(result["rsp"]["breakpoint_cleared"])
            self.assertTrue(result["rsp"]["detached"])
            self.assertTrue(raw_socket.closed)
            self.assertEqual(raw_socket.continue_timeouts, 1)
            self.assertEqual(raw_socket.interrupts, 1)
            self.assertIn(b"z0,2c0ee0,4", raw_socket.commands)
            self.assertIn(b"D", raw_socket.commands)
            self.assertTrue(process.terminated)
            self.assertTrue(result["listener_released"])
            self.assertTrue(result["stage_cleanup"]["removed"])
            self.assertFalse(Path(result["stage"]["run_dir"]).exists())
            self.assertTrue(result["stage"]["staged_save_changed"])
            self.assertIn("disposable runtime copy may change",
                          result["stage"]["staged_save_mutation_policy"])
            self.assertTrue(result["inputs"]["disposable_save_fixture_unchanged"])
            self.assertEqual(result.get("cleanup_errors", []), [])


if __name__ == "__main__":
    unittest.main()
