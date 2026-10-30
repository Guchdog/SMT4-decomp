import hashlib
import socket
import subprocess
import threading
import unittest
import os
from pathlib import Path
import tempfile
from unittest.mock import patch

from tools.h2_azahar_rsp_probe import (
    PINNED_AZAHAR_RPC_SHA256, PROFILE_SEED_FILES, ProbeError, Rsp, _stage_game_file,
    azahar_command, copy_pinned_package_assets, decode_r0, frame,
    listener_owner, parse_frame, parse_netstat_listener_rows, provision_profile,
    qt_plugin_diagnostics, r0_raw,
)


class StagedGameFileTests(unittest.TestCase):
    def test_hardlink_staging_preserves_hash_and_shared_file_identity(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "pinned-title.cci"
            destination = root / "stage" / "pinned-title.cci"
            destination.parent.mkdir()
            source.write_bytes(b"large immutable game image fixture")

            _stage_game_file(source, destination, hardlink=True)

            self.assertEqual(hashlib.sha256(source.read_bytes()).digest(),
                             hashlib.sha256(destination.read_bytes()).digest())
            self.assertTrue(os.path.samefile(source, destination))

    def test_default_staging_copies_and_hardlink_failure_is_clear(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "pinned-title.cci"
            destination = root / "stage" / "pinned-title.cci"
            destination.parent.mkdir()
            source.write_bytes(b"immutable fixture")

            _stage_game_file(source, destination)
            self.assertEqual(source.read_bytes(), destination.read_bytes())
            self.assertFalse(os.path.samefile(source, destination))
            with self.assertRaisesRegex(ProbeError, "could not hard-link staged game image"):
                _stage_game_file(source, destination, hardlink=True)


class RspEncodingTests(unittest.TestCase):
    def test_frame_round_trip_and_checksum_rejection(self):
        packet = frame(b"P0=78563412")
        self.assertEqual(parse_frame(packet), b"P0=78563412")
        with self.assertRaisesRegex(ProbeError, "checksum"):
            parse_frame(packet[:-1] + (b"0" if packet[-1:] != b"0" else b"1"))

    def test_r0_is_little_endian_and_exactly_four_bytes(self):
        self.assertEqual(r0_raw(0x12345678), bytes.fromhex("78563412"))
        self.assertEqual(decode_r0(b"78563412"), 0x12345678)
        with self.assertRaisesRegex(ProbeError, "4-byte"):
            decode_r0(b"7856")


class ListenerOwnershipTests(unittest.TestCase):
    def test_netstat_parser_reads_ipv4_and_ipv6_listener_rows(self):
        output = (
            "Active Connections\n"
            "  Proto  Local Address          Foreign Address        State           PID\n"
            "  TCP    127.0.0.1:58123       0.0.0.0:0              LISTENING       4200\n"
            "  TCP    [::1]:58123            [::]:0                 LISTENING       4200\n"
            "  TCP    127.0.0.1:58124       127.0.0.1:9            ESTABLISHED     4201\n"
        )
        self.assertEqual(parse_netstat_listener_rows(output), [
            ("127.0.0.1", 58123, 4200), ("::1", 58123, 4200),
        ])

    def test_netstat_parser_accepts_complete_localized_header(self):
        output = (
            "Conexiones activas\n"
            "  Proto  Dirección local          Dirección remota        Estado           PID\n"
            "  TCP    127.0.0.1:58123       0.0.0.0:0              LISTENING       4200\n"
        )
        self.assertEqual(parse_netstat_listener_rows(output), [
            ("127.0.0.1", 58123, 4200),
        ])

    def test_netstat_parser_rejects_missing_header_and_malformed_tcp_rows(self):
        with self.assertRaisesRegex(ProbeError, "Proto header"):
            parse_netstat_listener_rows("garbled output")
        with self.assertRaisesRegex(ProbeError, "malformed netstat TCP row"):
            parse_netstat_listener_rows(
                "Proto Local Address Foreign Address State PID\nTCP bad-row\n")
        with self.assertRaisesRegex(ProbeError, "malformed netstat address"):
            parse_netstat_listener_rows(
                "Proto Local Address Foreign Address State PID\n"
                "TCP host.invalid:58123 0.0.0.0:0 LISTENING 4200\n")

    def test_netstat_parser_rejects_bare_truncated_and_duplicate_headers(self):
        malformed_headers = (
            "Proto\n",
            "Proto Local Address Foreign Address State\n",
            "Proto Local Address Remote Address State PID\n",
        )
        for output in malformed_headers:
            with self.subTest(output=output), self.assertRaisesRegex(
                    ProbeError, "malformed netstat header"):
                parse_netstat_listener_rows(output)
        with self.assertRaisesRegex(ProbeError, "duplicate Proto header"):
            parse_netstat_listener_rows(
                "Proto Local Address Foreign Address State PID\n"
                "Proto Local Address Foreign Address State PID\n")
        # A complete header with no TCP rows is the valid empty-table case.
        self.assertEqual(parse_netstat_listener_rows(
            "Proto Local Address Foreign Address State PID\n"), [])

    def test_owner_query_rejects_ambiguous_or_non_loopback_listener_rows(self):
        header = "Proto Local Address Foreign Address State PID\n"
        with patch("tools.h2_azahar_rsp_probe.subprocess.run") as run:
            run.return_value.returncode = 0
            run.return_value.stderr = ""
            run.return_value.stdout = (
                header + "TCP 127.0.0.1:58123 0.0.0.0:0 LISTENING 4200\n"
                "TCP [::1]:58123 [::]:0 LISTENING 4201\n")
            with self.assertRaisesRegex(ProbeError, "multiple listener owners"):
                listener_owner(58123)
            run.return_value.stdout = header + "TCP 0.0.0.0:58123 0.0.0.0:0 LISTENING 4200\n"
            with self.assertRaisesRegex(ProbeError, "not loopback-only"):
                listener_owner(58123)

    def test_owner_query_fails_closed_on_timeout(self):
        with patch("tools.h2_azahar_rsp_probe.subprocess.run",
                   side_effect=subprocess.TimeoutExpired("netstat.exe", 3)):
            with self.assertRaisesRegex(ProbeError, "timed out"):
                listener_owner(58123)

    def test_free_loopback_port_returns_none(self):
        probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
        probe.close()
        self.assertIsNone(listener_owner(port))

    def test_owned_live_loopback_listener_reports_current_pid(self):
        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            listener.bind(("127.0.0.1", 0))
            listener.listen(1)
            port = listener.getsockname()[1]
            self.assertEqual(listener_owner(port), os.getpid())
        finally:
            listener.close()


class CommandTests(unittest.TestCase):
    def test_command_uses_only_short_gdb_flag_and_game_path(self):
        executable = Path("E:/stage/azahar.exe")
        game = Path("E:/stage/title.cci")
        self.assertEqual(
            azahar_command(executable, 58158, game),
            [str(executable), "-g", "58158", str(game)],
        )


class ProfileProvisioningTests(unittest.TestCase):
    def test_copies_only_approved_seed_files_and_records_matching_hashes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            seed = root / "seed"
            user = root / "stage" / "user"
            user.mkdir(parents=True)
            for relative, content in ((PROFILE_SEED_FILES[0], b"test-mac\n"),
                                      (PROFILE_SEED_FILES[1], b"test-config")):
                source = seed / relative
                source.parent.mkdir(parents=True, exist_ok=True)
                source.write_bytes(content)
            (seed / "sdmc").mkdir(parents=True)
            (seed / "sdmc" / "must-not-copy.sav").write_bytes(b"private-save")

            records = provision_profile(seed, user)

            expected = {relative.as_posix() for relative in PROFILE_SEED_FILES}
            actual = {path.relative_to(user).as_posix() for path in user.rglob("*") if path.is_file()}
            self.assertEqual(actual, expected)
            self.assertEqual(len(records), 2)
            for record in records:
                self.assertEqual(record["source_sha256_before"], record["staged_sha256"])
                self.assertEqual(record["source_sha256_before"], record["source_sha256_after_copy"])
                self.assertTrue(record["source_unchanged_after_copy"])

    def test_refuses_to_provision_nonempty_user_tree(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            seed = root / "seed"
            user = root / "user"
            seed.mkdir()
            user.mkdir()
            (user / "unexpected").write_text("keep", encoding="utf-8")
            with self.assertRaisesRegex(ProbeError, "must exist and be empty"):
                provision_profile(seed, user)


class PackageProvenanceTests(unittest.TestCase):
    def test_copies_only_the_pinned_scripting_asset(self):
        source_root = Path(r"E:\emulador3ds")
        source = source_root / "scripting" / "AzaharRPC.py"
        self.assertTrue(source.is_file())
        self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),
                         PINNED_AZAHAR_RPC_SHA256)
        with tempfile.TemporaryDirectory() as temporary:
            app = Path(temporary) / "app"
            app.mkdir()
            records = copy_pinned_package_assets(source_root, app)
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0]["staged_sha256"], PINNED_AZAHAR_RPC_SHA256)
            self.assertEqual((app / "scripting" / "AzaharRPC.py").read_bytes(), source.read_bytes())
            self.assertEqual([p.relative_to(app).as_posix() for p in app.rglob("*") if p.is_file()],
                             ["scripting/AzaharRPC.py"])

    def test_qt_plugin_filter_keeps_platform_and_plugin_diagnostics(self):
        lines = ["QFactoryLoader::QFactoryLoader() checking path",
                 "platform plugin qwindows.dll loaded", "unrelated normal line"]
        self.assertEqual(qt_plugin_diagnostics(lines), lines[:2])


class RspClientTests(unittest.TestCase):
    def test_same_value_p_packet_round_trip_against_local_stub(self):
        client_sock, server_sock = socket.socketpair()
        expected_r0 = bytes.fromhex("78563412")
        packets = []

        def read_frame(sock):
            while sock.recv(1) != b"$":
                pass
            body = bytearray()
            while True:
                char = sock.recv(1)
                if char == b"#":
                    break
                body.extend(char)
            tail = sock.recv(2)
            return parse_frame(b"$" + bytes(body) + b"#" + tail)

        def stub():
            try:
                while True:
                    payload = read_frame(server_sock)
                    packets.append(payload)
                    server_sock.sendall(b"+")
                    if payload == b"p0":
                        reply = expected_r0.hex().encode("ascii")
                    elif payload == b"P0=" + expected_r0.hex().encode("ascii"):
                        reply = b"OK"
                    else:
                        reply = b"E01"
                    server_sock.sendall(frame(reply))
                    if server_sock.recv(1) != b"+":
                        return
                    if payload.startswith(b"P0="):
                        return
            finally:
                server_sock.close()

        thread = threading.Thread(target=stub, daemon=True)
        thread.start()
        rsp = Rsp(client_sock, timeout=1)
        before = decode_r0(rsp.request(b"p0"))
        self.assertEqual(rsp.request(b"P0=" + r0_raw(before).hex().encode("ascii")), b"OK")
        self.assertEqual(before, 0x12345678)
        self.assertEqual(packets, [b"p0", b"P0=78563412"])
        client_sock.close()
        thread.join(timeout=1)
        self.assertFalse(thread.is_alive())

    def test_unexpected_ack_fails_closed(self):
        client_sock, server_sock = socket.socketpair()

        def stub():
            read = server_sock.recv(128)
            self.assertTrue(read.startswith(b"$qSupported"))
            server_sock.sendall(b"-")
            server_sock.close()

        thread = threading.Thread(target=stub, daemon=True)
        thread.start()
        with self.assertRaisesRegex(ProbeError, "acknowledgement"):
            Rsp(client_sock, timeout=1).request(b"qSupported")
        client_sock.close()
        thread.join(timeout=1)


if __name__ == "__main__":
    unittest.main()
