#!/usr/bin/env python3
"""Print one-shot execution flags for a selected semantic-experiment batch."""

from __future__ import annotations

import argparse
import socket
import sys


HOST = "127.0.0.1"
PORT = 24689
BATCH_BREAKPOINTS = {
    # Historical Azahar-installed patch. Keep batch 2 as the safe CLI default.
    2: {
        0x003FE624: (0x00128F34, "relative_pointer"),
        0x003FE634: (0x002AE464, "unsigned_threshold"),
        0x003FE648: (0x00394614, "byte_equality"),
        0x003FE65C: (0x0038143C, "halfword_cursor"),
        0x003FE670: (0x00381450, "byte_cursor"),
        0x003FE684: (0x003D7228, "three_word_copy"),
        0x003FE694: (0x0037C46C, "state_flags"),
        0x003FE6B4: (0x00121D70, "signed_byte_field"),
        0x003FE6C0: (0x0014EC5C, "nullable_pointer_field"),
        0x003FE6D0: (0x00131414, "paired_word_store"),
    },
    # Current batch-4 report manifest; this image has not been installed by the
    # monitor and must be selected only when Azahar is running that exact patch.
    4: {
        0x003FE624: (0x00128F34, "relative_pointer"),
        0x003FE634: (0x002AE464, "unsigned_threshold"),
        0x003FE648: (0x00394614, "byte_equality"),
        0x003FE65C: (0x0038143C, "halfword_cursor"),
        0x003FE670: (0x00381450, "byte_cursor"),
        0x003FE684: (0x003D7228, "three_word_copy"),
        0x003FE694: (0x0037C46C, "state_flags"),
        0x003FE6B4: (0x00121D70, "signed_byte_field"),
        0x003FE6C0: (0x0014EC5C, "nullable_pointer_field"),
        0x003FE6D0: (0x00131414, "paired_word_store"),
        0x003FE6DC: (0x0023E4D4, "ui_flag_predicate"),
        0x003FE6EC: (0x002C4BF0, "ui_widget_flag_or"),
        0x003FE6FC: (0x00357A28, "ui_id_pack"),
        0x003FE70C: (0x002ADB40, "two_word_copy"),
    },
}
# Backwards-compatible name for callers that imported the historical table.
BREAKPOINTS = BATCH_BREAKPOINTS[2]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--batch",
        choices=("2", "4"),
        default="2",
        help="replacement manifest to monitor (default: 2, the historically installed patch)",
    )
    parser.add_argument(
        "--pid",
        default="11",
        help="Azahar emulated process ID (default: 11, read from azahar_log.txt)",
    )
    return parser.parse_args(argv)


class RSP:
    def __init__(self, sock: socket.socket) -> None:
        self.sock = sock
        self.no_ack = False

    def _read_byte(self) -> bytes:
        value = self.sock.recv(1)
        if not value:
            raise ConnectionError("Azahar closed the GDB connection")
        return value

    def _read_packet(self) -> str:
        while True:
            char = self._read_byte()
            if char == b"$":
                break
            if char == b"%":
                # RSP notifications can precede the response we are waiting for.
                continue
        payload = bytearray()
        checksum = 0
        while True:
            char = self._read_byte()
            if char == b"#":
                break
            payload.extend(char)
            checksum = (checksum + char[0]) & 0xFF
        expected = int(self.sock.recv(2), 16)
        if checksum != expected:
            if not self.no_ack:
                self.sock.sendall(b"-")
            raise ConnectionError("Azahar sent a packet with an invalid checksum")
        if not self.no_ack:
            self.sock.sendall(b"+")
        return payload.decode("ascii", errors="replace")

    def command(self, payload: str) -> str:
        encoded = payload.encode("ascii")
        packet = b"$" + encoded + b"#" + f"{sum(encoded) & 0xFF:02x}".encode()
        self.sock.sendall(packet)
        if not self.no_ack:
            while True:
                ack = self._read_byte()
                if ack == b"+":
                    break
                if ack == b"-":
                    self.sock.sendall(packet)
                # Ignore stray console output or notifications before the ACK.
        response = self._read_packet()
        if payload == "QStartNoAckMode" and response == "OK":
            self.no_ack = True
        return response


def _read_pc(rsp: RSP) -> int | None:
    raw = rsp.command("p0f")
    if len(raw) != 8:
        return None
    try:
        return int.from_bytes(bytes.fromhex(raw), "little")
    except ValueError:
        return None


def _identify(pc: int | None, active: set[int]) -> tuple[int, int] | None:
    if pc is None:
        return None
    # ARM exception PCs may identify the trapped instruction or the next one.
    matches = [
        (address, abs(pc - address))
        for address in active
        if pc in (address, address + 4, address + 8)
    ]
    return min(matches, key=lambda match: match[1]) if matches else None


def main() -> int:
    args = parse_args()
    breakpoints = BATCH_BREAKPOINTS[int(args.batch)]
    print(f"Connecting to Azahar GDB stub at {HOST}:{PORT}...", flush=True)
    try:
        sock = socket.create_connection((HOST, PORT), timeout=5)
    except OSError as exc:
        print(f"Cannot connect: {exc}", file=sys.stderr)
        return 2

    sock.settimeout(None)
    rsp = RSP(sock)
    active: set[int] = set()
    try:
        capabilities = rsp.command(
            "qSupported:multiprocess+;swbreak+;hwbreak+;QStartNoAckMode+"
        )
        if not capabilities:
            raise ConnectionError("Azahar returned no RSP capabilities")
        if "QStartNoAckMode+" in capabilities:
            rsp.command("QStartNoAckMode")

        extended = rsp.command("!")
        if extended != "OK":
            raise RuntimeError(f"Azahar rejected extended mode: {extended!r}")
        pid = int(args.pid, 0)
        attached = rsp.command(f"vAttach;{pid:x}")
        if not attached.startswith("T"):
            raise RuntimeError(
                f"Could not attach to emulated process {args.pid}: {attached!r}"
            )

        for address in breakpoints:
            result = rsp.command(f"Z0,{address:x},4")
            if result != "OK":
                raise RuntimeError(
                    f"Azahar rejected breakpoint 0x{address:08X}: {result!r}"
                )
            active.add(address)

        print(f"Attached to process {args.pid}; armed {len(active)} one-shot flags "
              f"for batch {args.batch}. "
              "Play normally; press Ctrl+C to stop.", flush=True)
        while active:
            stop = rsp.command("c")
            pc = _read_pc(rsp)
            hit = _identify(pc, active)
            if hit is None:
                pc_text = "unavailable" if pc is None else f"0x{pc:08X}"
                print(f"Stopped (PC {pc_text}, reply {stop!r}); resuming.", flush=True)
                continue

            address, _ = hit
            original, name = breakpoints[address]
            rsp.command(f"z0,{address:x},4")
            active.remove(address)
            print(
                f"FLAG: {name} replacement for 0x{original:08X} "
                f"executed at 0x{address:08X} ({len(active)} flags remain)",
                flush=True,
            )
        print(f"All {len(breakpoints)} batch-{args.batch} replacement entries were observed. "
              "This confirms entry reachability only, not behavioral equivalence.", flush=True)
        return 0
    except KeyboardInterrupt:
        print("\nStopping flag monitor and resuming Azahar...", flush=True)
        return 130
    except (ConnectionError, OSError, RuntimeError, ValueError) as exc:
        print(f"Flag monitor error: {exc}", file=sys.stderr)
        return 1
    finally:
        # Remove remaining software breakpoints and detach so the game resumes.
        try:
            for address in tuple(active):
                rsp.command(f"z0,{address:x},4")
            rsp.command("D")
        except (ConnectionError, OSError, ValueError):
            pass
        sock.close()


if __name__ == "__main__":
    raise SystemExit(main())
