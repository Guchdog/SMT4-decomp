import sys
import unittest
from unittest.mock import patch
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.h2_autonomous_gdb_verify import (
    ProbeError,
    compare_h2_lifecycle,
    detach_rsp_for_clean_shutdown,
    prepare_runtime_qt_config,
    profile_snapshot_delta,
    runtime_dependency_manifest,
    wait_for_calc_state,
)


def run_result(*, persisted: bool, restart_config: str = "base", restart_work: str = "work",
               reentered: bool = False, ready: bool = False, clean: bool = True) -> dict:
    return {
        "same_session_reentry_proven": reentered,
        "same_session_reentry": (
            {"g_ConfigBytes_hex": "confirmed", "TitleConfigWork_normalized_sha256": "same"}
            if reentered else None
        ),
        "post_confirm_readiness_trace": {"completed": ready},
        "restart_reentry": {
            "g_ConfigBytes_hex": restart_config,
            "TitleConfigWork_normalized_sha256": restart_work,
            "state_08": 1,
            "bgm_28": 7,
            "se_2c": 7,
            "voice_30": 7,
        },
        "restart_persistence_match": persisted,
        "clean_shutdown": {"clean_exit": clean},
        "restart_clean_shutdown": {"clean_exit": clean},
    }


class FakeRsp:
    def __init__(self, reply: bytes = b""):
        self.reply = reply
        self.packets = []

    def request(self, packet: bytes) -> bytes:
        self.packets.append(packet)
        return self.reply


class H2AutonomousLifecycleTests(unittest.TestCase):
    def test_runtime_qt_config_disables_only_staged_exit_prompt(self):
        raw = (
            b"frame_limit\\default=true\nframe_limit=100\n"
            b"use_vsync\\default=true\nuse_vsync=true\n"
            b"confirmClose\\default=true\nconfirmClose=true\n"
        )
        changed = prepare_runtime_qt_config(raw)
        self.assertIn(b"frame_limit\\default=false", changed)
        self.assertIn(b"frame_limit=0", changed)
        self.assertIn(b"use_vsync\\default=false", changed)
        self.assertIn(b"use_vsync=false", changed)
        self.assertIn(b"confirmClose\\default=false", changed)
        self.assertIn(b"confirmClose=false", changed)
        self.assertNotIn(b"confirmClose=true", changed)

    def test_clean_shutdown_detaches_rsp_first(self):
        rsp = FakeRsp(b"OK")
        self.assertEqual(detach_rsp_for_clean_shutdown(rsp), "OK")
        self.assertEqual(rsp.packets, [b"D"])

    def test_clean_shutdown_detach_fails_closed(self):
        rsp = FakeRsp(b"E01")
        with self.assertRaisesRegex(ProbeError, "detach failed"):
            detach_rsp_for_clean_shutdown(rsp)
        self.assertEqual(rsp.packets, [b"D"])

    def test_calc_state_wait_returns_when_target_is_observed(self):
        fake_rsp = FakeRsp()
        with (
            patch("tools.h2_autonomous_gdb_verify.run_to_bp") as run_to_bp,
            patch(
                "tools.h2_autonomous_gdb_verify.rsp_read_u32",
                side_effect=[0x2000, 1],
            ),
            patch("tools.h2_autonomous_gdb_verify.decode_r0", return_value=0x1234),
        ):
            self.assertEqual(
                wait_for_calc_state(fake_rsp, target_state=1, max_polls=1), 0x2000
            )
        run_to_bp.assert_called_once_with(fake_rsp, 0x001EA928)

    def test_calc_state_wait_fails_after_poll_bound(self):
        fake_rsp = FakeRsp()
        with (
            patch("tools.h2_autonomous_gdb_verify.run_to_bp") as run_to_bp,
            patch(
                "tools.h2_autonomous_gdb_verify.rsp_read_u32",
                side_effect=[0x2000, 0, 0x2000, 0],
            ),
            patch("tools.h2_autonomous_gdb_verify.decode_r0", return_value=0x1234),
        ):
            with self.assertRaisesRegex(ProbeError, "after 2 Calc polls"):
                wait_for_calc_state(fake_rsp, target_state=1, max_polls=2)
        self.assertEqual(run_to_bp.call_count, 4)


    def test_matching_reset_behavior_is_parity_not_a_failure(self):
        result = compare_h2_lifecycle(
            run_result(persisted=False, restart_config="reset"),
            run_result(persisted=False, restart_config="reset"),
        )
        self.assertTrue(result["paired_lifecycle_behavior_matched"])
        self.assertFalse(result["restart_matches_confirmation_original"])
        self.assertFalse(result["restart_matches_confirmation_patched"])
        self.assertFalse(result["full_controlled_lifecycle_completed"])

    def test_persisted_original_and_patched_behavior_also_matches(self):
        result = compare_h2_lifecycle(
            run_result(persisted=True, restart_config="confirmed"),
            run_result(persisted=True, restart_config="confirmed"),
        )
        self.assertTrue(result["paired_lifecycle_behavior_matched"])
        self.assertTrue(result["restart_persistence_outcome_matched"])

    def test_original_patched_persistence_divergence_fails(self):
        result = compare_h2_lifecycle(
            run_result(persisted=False, restart_config="reset"),
            run_result(persisted=True, restart_config="reset"),
        )
        self.assertFalse(result["paired_lifecycle_behavior_matched"])
        self.assertFalse(result["restart_persistence_outcome_matched"])

    def test_restart_state_divergence_fails(self):
        result = compare_h2_lifecycle(
            run_result(persisted=False, restart_config="reset"),
            run_result(persisted=False, restart_config="different"),
        )
        self.assertFalse(result["restart_state_matched_original_vs_patched"])
        self.assertFalse(result["paired_lifecycle_behavior_matched"])

    def test_missing_restart_state_fails_closed(self):
        original = run_result(persisted=False)
        patched = run_result(persisted=False)
        original["restart_reentry"] = None
        patched["restart_reentry"] = None
        result = compare_h2_lifecycle(original, patched)
        self.assertFalse(result["restart_state_matched_original_vs_patched"])
        self.assertFalse(result["paired_lifecycle_behavior_matched"])

    def test_incomplete_shutdown_fails(self):
        result = compare_h2_lifecycle(
            run_result(persisted=False, clean=False),
            run_result(persisted=False, clean=True),
        )
        self.assertFalse(result["clean_shutdowns_matched"])
        self.assertFalse(result["paired_lifecycle_behavior_matched"])

    def test_profile_delta_identifies_saved_file_change(self):
        self.assertEqual(
            profile_snapshot_delta({"config": "old", "kept": "same"},
                                   {"config": "new", "added": "hash"}),
            {"added": ["added"], "removed": ["kept"], "changed": ["config"]},
        )

    def test_runtime_dependency_manifest_hashes_only_staged_assets(self):
        import tempfile

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            executable = root / "azahar.exe"
            executable.write_bytes(b"unused executable marker")
            (root / "Qt6Core.dll").write_bytes(b"core")
            plugin_dir = root / "plugins" / "platforms"
            plugin_dir.mkdir(parents=True)
            (plugin_dir / "qwindows.dll").write_bytes(b"platform")
            manifest = runtime_dependency_manifest(executable)
            self.assertEqual(
                [item["staged_relative_path"] for item in manifest],
                ["plugins/platforms/qwindows.dll", "Qt6Core.dll"],
            )
            self.assertEqual([item["size"] for item in manifest], [8, 4])


if __name__ == "__main__":
    unittest.main(verbosity=2)
