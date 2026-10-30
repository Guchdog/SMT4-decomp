import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from tools import h2_apt_utility4_caller_probe as probe
from tests.test_h2_apt_utility4_tailstep_probe import CaptureRsp


class FatalExecuteIntegrationTests(unittest.TestCase):
    def _run_lost_breakpoint_reply(self, fail_first_termination, *, persistent_failure=False,
                                   poll_failure_after_first=False):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            output = root / "packet"
            output.mkdir()
            source_exe, source_game, fixture = (root / "azahar.exe", root / "game.cci", root / "fixture.sav")
            source_exe.write_bytes(b"synthetic executable")
            source_game.write_bytes(b"synthetic game")
            fixture.write_bytes(b"synthetic save")
            seed = root / "seed"
            seed.mkdir()
            (seed / "marker").write_bytes(b"synthetic profile")
            events = []

            class Process:
                pid = 4321
                returncode = None
                termination_attempts = 0

                def poll(self):
                    if poll_failure_after_first and self.termination_attempts:
                        raise RuntimeError("simulated poll failure")
                    return self.returncode

                def terminate(self):
                    self.termination_attempts += 1
                    events.append(b"<termination-attempt>")
                    if persistent_failure or (fail_first_termination and self.termination_attempts == 1):
                        raise RuntimeError("simulated first termination failure")
                    events.append(b"<child-stopped>")
                    self.returncode = 0

                def wait(self, timeout=None):
                    return self.returncode

                def kill(self):
                    events.append(b"<child-killed>")
                    self.returncode = -9

            process = Process()
            rsp = CaptureRsp(f"Z0,{probe.BREAKPOINT:x},4".encode("ascii"))
            rsp.commands = events
            rsp.sock.commands = events
            info = {"task": {"task": {"id": probe.RUNTIME_TASK_ID}}, "packet_root": output,
                    "source_exe": source_exe, "game": source_game, "fixture": fixture,
                    "profile_seed": seed, "runtime_dependencies": {"source_root": str(root), "assets": []}}
            record = {"output_root": str(output),
                      "private_azahar": {"observed_binary_sha256": probe.sha256(source_exe)},
                      "inputs": {"game_sha256": probe.sha256(source_game),
                                 "disposable_save_fixture_sha256": probe.sha256(fixture),
                                 "profile_seed_files": probe.shared.file_manifest(seed)}}
            args = SimpleNamespace(startup_timeout=1.0, capture_timeout=1.0, packet_timeout=0.5,
                                   port=38765, max_hits=1, output_root=None)

            def stage_runtime(_exe, game, _seed, save, stage, _dependencies):
                app = stage / "app"
                user = app / "user"
                user.mkdir(parents=True)
                exe = app / "azahar.exe"
                exe.write_bytes(source_exe.read_bytes())
                staged_game = stage / "pinned-title.cci"
                staged_game.write_bytes(game.read_bytes())
                staged_save = user / probe.SAVE_REL
                staged_save.parent.mkdir(parents=True)
                staged_save.write_bytes(save.read_bytes())
                return {"run_dir": str(stage), "executable": exe, "game": staged_game,
                        "app_dir": app, "user_dir": user, "profile_files": [], "package_assets": [],
                        "runtime_files_before": probe.shared.file_manifest(app, excluded_top_level={"user"}),
                        "staged_save_path": staged_save, "staged_save_sha256_before": probe.sha256(staged_save)}

            with (patch.object(probe, "validate_task_and_inputs", return_value=info),
                  patch.object(probe.shared, "reserve_port"),
                  patch.object(probe, "stage_runtime", side_effect=stage_runtime),
                  patch.object(probe, "runtime_launch_paths", side_effect=lambda s: (s["executable"], s["game"], 100)),
                  patch.object(probe, "staged_alias_log_evidence", return_value={"profile_path_in_log": True, "title_id_in_log": True}),
                  patch.object(probe.subprocess, "Popen", return_value=process),
                  patch.object(probe, "listener_binding", side_effect=[{"local_address": "127.0.0.1", "local_port": 38765, "pid": 4321}, None]),
                  patch.object(probe, "connect_to_loopback", return_value=rsp.sock),
                  patch.object(probe, "DeadlineRsp", return_value=rsp)):
                with self.assertRaisesRegex(probe.ProbeError, "lost reply") as caught:
                    probe.execute(args, record)

            self.assertNotIn(b"D", events)
            if persistent_failure or poll_failure_after_first:
                self.assertNotIn(b"<child-stopped>", events)
                self.assertNotIn(b"<socket-close>", events)
                self.assertFalse(rsp.sock.closed)
                self.assertFalse(record["stage_cleanup"]["removed"])
                self.assertFalse(record["process_cleanup"]["confirmed_stopped"])
                self.assertIn("child process may still be running", record["stage_cleanup"]["error"])
                self.assertTrue(record.get("cleanup_errors"))
            else:
                self.assertLess(events.index(b"<child-stopped>"), events.index(b"<socket-close>"))
                self.assertTrue(record["stage_cleanup"]["removed"])
                self.assertTrue(record["process_cleanup"]["confirmed_stopped"])
            if fail_first_termination and not (persistent_failure or poll_failure_after_first):
                self.assertIn("simulated first termination failure", str(caught.exception))
                self.assertEqual(process.termination_attempts, 2)
                self.assertTrue(record["process_cleanup"]["terminated"])
            elif not fail_first_termination and not persistent_failure:
                self.assertTrue(record["rsp_fatal_process_cleanup"]["terminated"])
            self.assertTrue(record["inputs"]["disposable_save_fixture_unchanged"])
            self.assertTrue(record["inputs"]["game_unchanged"])
            self.assertTrue(record["inputs"]["source_executable_unchanged"])
            self.assertTrue(record["inputs"]["profile_seed_unchanged"])
            self.assertTrue(record["inputs"]["runtime_dependency_sources_unchanged"])
            self.assertFalse(record["stage"]["staged_save_changed"])
            self.assertTrue(record["stage"]["runtime_files_unchanged_after_run"])
            self.assertEqual(fixture.read_bytes(), b"synthetic save")

    def test_lost_breakpoint_reply_stops_child_before_socket_close(self):
        self._run_lost_breakpoint_reply(False)

    def test_failed_fatal_stop_is_retried_before_socket_close(self):
        self._run_lost_breakpoint_reply(True)

    def test_persistent_termination_failure_preserves_socket_and_stage(self):
        self._run_lost_breakpoint_reply(True, persistent_failure=True)

    def test_poll_errors_preserve_socket_and_stage(self):
        self._run_lost_breakpoint_reply(True, poll_failure_after_first=True)


if __name__ == "__main__":
    unittest.main()
