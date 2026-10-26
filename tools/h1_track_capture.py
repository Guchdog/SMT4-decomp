#!/usr/bin/env python3
"""Read-only, bounded Azahar GDB capture for the two H1 animation callbacks."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import select
import socket
import struct
import time

ROOT = Path(__file__).resolve().parents[1]
HOST = "127.0.0.1"
PORT = 24689
BREAKPOINTS = {
    0x001EA0CC: "gate_a_call",
    0x001EA0DC: "gate_b_call",
    0x002872B0: "gate_a_positive_body",
    0x002872E4: "gate_a_callback_call",
    0x0020FFAC: "gate_b_positive_body",
    0x00210010: "gate_b_callback_call",
    0x002A5CB8: "track_setup_source",
    0x002A5D0C: "track_setup_after_callback_store",
    0x001540C0: "render_bind_source",
    0x001540E0: "render_bind_after_callback_store",
}
GATE_CALLS = {"gate_a_callback_call", "gate_b_callback_call"}


class RSP:
    def __init__(self, sock: socket.socket) -> None:
        self.sock = sock
        self.no_ack = False
        self.buffer = bytearray()

    def _packet(self, payload: str) -> bytes:
        raw = payload.encode("ascii")
        return b"$" + raw + b"#" + f"{sum(raw) & 0xff:02x}".encode()

    def _extract_packet(self) -> str | None:
        while self.buffer and self.buffer[0] in b"+\r\n":
            del self.buffer[0]
        start = self.buffer.find(b"$")
        if start < 0:
            self.buffer.clear()
            return None
        if start:
            del self.buffer[:start]
        end = self.buffer.find(b"#", 1)
        if end < 0 or len(self.buffer) < end + 3:
            return None
        payload = bytes(self.buffer[1:end])
        expected = int(bytes(self.buffer[end + 1:end + 3]), 16)
        if sum(payload) & 0xff != expected:
            raise ConnectionError("Azahar sent an invalid GDB packet checksum")
        del self.buffer[:end + 3]
        return payload.decode("ascii", errors="replace")

    def _receive(self, timeout: float) -> str:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            packet = self._extract_packet()
            if packet is not None:
                if not self.no_ack:
                    self.sock.sendall(b"+")
                return packet
            readable, _, _ = select.select([self.sock], [], [], max(0, deadline - time.monotonic()))
            if not readable:
                break
            chunk = self.sock.recv(4096)
            if not chunk:
                raise ConnectionError("Azahar closed the GDB connection")
            self.buffer.extend(chunk)
        raise TimeoutError("Timed out waiting for Azahar GDB")

    def command(self, payload: str, timeout: float = 5.0) -> str:
        self.sock.sendall(self._packet(payload))
        if not self.no_ack:
            deadline = time.monotonic() + timeout
            while time.monotonic() < deadline:
                readable, _, _ = select.select([self.sock], [], [], max(0, deadline-time.monotonic()))
                if not readable:
                    break
                ack = self.sock.recv(1)
                if ack == b"+":
                    break
                if ack == b"-":
                    self.sock.sendall(self._packet(payload))
            else:
                raise TimeoutError("Timed out waiting for GDB command acknowledgement")
        result = self._receive(timeout)
        if payload == "QStartNoAckMode" and result == "OK":
            self.no_ack = True
        return result

    def continue_for(self, seconds: float) -> str | None:
        self.sock.sendall(self._packet("c"))
        if not self.no_ack:
            deadline = time.monotonic() + 5
            while time.monotonic() < deadline:
                readable, _, _ = select.select([self.sock], [], [], max(0, deadline-time.monotonic()))
                if not readable:
                    break
                ack = self.sock.recv(1)
                if ack == b"+":
                    break
                if ack == b"-":
                    self.sock.sendall(self._packet("c"))
            else:
                raise TimeoutError("Timed out waiting for continue acknowledgement")
        try:
            return self._receive(seconds)
        except TimeoutError:
            # Interrupt only the emulated process, then return it to the normal
            # running state when detach clears the temporary software traps.
            self.sock.sendall(b"\x03")
            return self._receive(5.0)

    def reg(self, index: int) -> int | None:
        raw = self.command(f"p{index:x}")
        try:
            data = bytes.fromhex(raw)
        except ValueError:
            return None
        return int.from_bytes(data, "little") if len(data) == 4 else None

    def memory(self, address: int | None, size: int) -> bytes | None:
        if address is None or address <= 0 or address + size > 0x100000000:
            return None
        raw = self.command(f"m{address:x},{size:x}")
        try:
            data = bytes.fromhex(raw)
        except ValueError:
            return None
        return data if len(data) == size else None

    def u32(self, address: int | None) -> int | None:
        data = self.memory(address, 4)
        return struct.unpack("<I", data)[0] if data is not None else None

    def u8(self, address: int | None) -> int | None:
        data = self.memory(address, 1)
        return data[0] if data is not None else None


def _hex(value: int | None) -> str | None:
    return None if value is None else f"0x{value:08x}"


def _identify(pc: int | None) -> tuple[int, str] | None:
    if pc is None:
        return None
    matches = [(address, name) for address, name in BREAKPOINTS.items()
               if pc in (address, address + 4, address + 8)]
    return min(matches, key=lambda item: abs(pc - item[0])) if matches else None


def capture_event(rsp: RSP, name: str, pc: int, pending: dict) -> dict:
    regs = {f"r{i}": _hex(rsp.reg(i)) for i in range(6)}
    event: dict = {"time_utc": datetime.now(timezone.utc).isoformat(),
                   "breakpoint": name, "pc": _hex(pc), "registers": regs}
    r0, r1, r4 = (rsp.reg(0), rsp.reg(1), rsp.reg(4))
    if name in {"gate_a_call", "gate_a_positive_body"}:
        child = r0
        obj = rsp.u32(child + 0x4c) if child else None
        event["child"] = _hex(child)
        event["child_gate_signed"] = _signed(rsp.u32(child + 0x34) if child else None)
        event["child_object"] = _hex(obj)
        if name == "gate_a_positive_body":
            event.update({"callback_target": _hex(rsp.u32(obj + 0x4c) if obj else None),
                          "callback_argument": _hex(rsp.u32(obj + 0x50) if obj else None),
                          "object_fields": _read_fields(rsp, obj, (0x38, 0x3c, 0x44, 0x48, 0x58))})
    elif name == "gate_b_call" or name == "gate_b_positive_body":
        child = r0
        model_data = rsp.u32(child + 0x2c) if child else None
        event["child"] = _hex(child)
        event["child_gate_signed"] = _signed(rsp.u32(child + 0x58) if child else None)
        event["model_data"] = _hex(model_data)
        if name == "gate_b_positive_body" and model_data:
            grid_desc = rsp.u32(model_data + 0x28)
            index = rsp.u32(model_data + 0x14c)
            stride = rsp.u32(grid_desc + 0x28) if grid_desc else None
            base = rsp.u32(grid_desc + 0x1c) if grid_desc else None
            record = rsp.u32(base + index * stride * 4) if base is not None and index is not None and stride is not None else None
            event.update({"grid_descriptor": _hex(grid_desc), "grid_index": index,
                          "grid_stride": stride, "grid_pointer_array": _hex(base),
                          "selected_record": _hex(record),
                          "callback_target": _hex(rsp.u32(record + 0x4c) if record else None),
                          "callback_argument": _hex(rsp.u32(record + 0x50) if record else None),
                          "record_fields": _read_fields(rsp, record, (0x38, 0x3c, 0x44, 0x48, 0x58))})
    elif name == "track_setup_source":
        descriptor = r1
        source = rsp.u32(descriptor) if descriptor else None
        pending["track_setup"] = {"track": r4, "source": source,
                                   "source_type": rsp.u8(source + 0x10) if source else None}
        event.update({"descriptor": _hex(descriptor), "track": _hex(r4),
                      "source": _hex(source),
                      "source_plus_0x10": pending["track_setup"]["source_type"]})
    elif name == "track_setup_after_callback_store":
        source = pending.get("track_setup", {})
        event.update({"track": _hex(r4), "callback_target": _hex(rsp.u32(r4 + 0x4c) if r4 else None),
                      "source": _hex(source.get("source")),
                      "source_plus_0x10": source.get("source_type")})
    elif name == "render_bind_source":
        source = r0
        pending["render_bind"] = {"object": r4, "source": source,
                                   "source_type": rsp.u8(source + 0x10) if source else None}
        event.update({"render_object": _hex(r4), "source": _hex(source),
                      "source_plus_0x10": pending["render_bind"]["source_type"]})
    elif name == "render_bind_after_callback_store":
        source = pending.get("render_bind", {})
        event.update({"render_object": _hex(r4), "callback_target": _hex(rsp.u32(r4 + 0x4c) if r4 else None),
                      "source": _hex(source.get("source")),
                      "source_plus_0x10": source.get("source_type")})
    elif name == "gate_a_callback_call":
        obj = r4
        event.update({"object": _hex(obj), "callback_target": _hex(r1),
                      "callback_argument": _hex(r0),
                      "object_callback_slot": _hex(rsp.u32(obj + 0x4c) if obj else None),
                      "object_callback_argument_slot": _hex(rsp.u32(obj + 0x50) if obj else None),
                      "object_fields": _read_fields(rsp, obj, (0x38, 0x3c, 0x44, 0x48, 0x58))})
    elif name == "gate_b_callback_call":
        record = r4
        event.update({"record": _hex(record), "callback_target": _hex(r1),
                      "callback_argument": _hex(r0),
                      "record_callback_slot": _hex(rsp.u32(record + 0x4c) if record else None),
                      "record_callback_argument_slot": _hex(rsp.u32(record + 0x50) if record else None),
                      "record_fields": _read_fields(rsp, record, (0x38, 0x3c, 0x44, 0x48, 0x58))})
    return event


def _read_fields(rsp: RSP, base: int | None, offsets: tuple[int, ...]) -> dict:
    if base is None:
        return {}
    return {f"+0x{offset:x}": _hex(rsp.u32(base + offset)) for offset in offsets}


def _signed(value: int | None) -> int | None:
    if value is None:
        return None
    return value - 0x100000000 if value & 0x80000000 else value


def run(pid: int, timeout: float, output: Path) -> dict:
    game_info = json.loads((ROOT / "config/game_info.json").read_text(encoding="utf-8"))
    digest = game_info["code_sha256"]
    sock = socket.create_connection((HOST, PORT), timeout=5)
    rsp = RSP(sock)
    armed: list[int] = []
    events: list[dict] = []
    seen: set[str] = set()
    pending: dict = {}
    error = None
    stopped_by_timeout = False
    try:
        capabilities = rsp.command("qSupported:multiprocess+;swbreak+;hwbreak+;QStartNoAckMode+")
        if "QStartNoAckMode+" in capabilities:
            if rsp.command("QStartNoAckMode") != "OK":
                raise RuntimeError("Azahar rejected no-ack mode")
        if rsp.command("!") != "OK":
            raise RuntimeError("Azahar rejected GDB extended mode")
        attached = rsp.command(f"vAttach;{pid:x}")
        if not attached.startswith("T"):
            raise RuntimeError(f"Could not attach to emulated process {pid}: {attached!r}")
        for address in BREAKPOINTS:
            if rsp.command(f"Z0,{address:x},4") != "OK":
                raise RuntimeError(f"Azahar rejected breakpoint {_hex(address)}")
            armed.append(address)

        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            reply = rsp.continue_for(max(0.1, deadline - time.monotonic()))
            if reply is None:
                stopped_by_timeout = True
                break
            pc = rsp.reg(15)
            hit = _identify(pc)
            if hit is None:
                if reply.startswith("T02"):
                    stopped_by_timeout = True
                    break
                continue
            address, name = hit
            if name in seen:
                # A title callback runs every frame. Keep only its first sample
                # and remove its temporary trap so observation stays bounded.
                rsp.command(f"z0,{address:x},4")
                if address in armed:
                    armed.remove(address)
                continue
            event = capture_event(rsp, name, pc or address, pending)
            events.append(event)
            seen.add(name)
            print(f"CAPTURE {name}: {json.dumps(event, separators=(',', ':'))}", flush=True)
            if name in GATE_CALLS and all(item in seen for item in GATE_CALLS):
                break
            if address in armed:
                rsp.command(f"z0,{address:x},4")
                armed.remove(address)
        else:
            stopped_by_timeout = True
    except (ConnectionError, OSError, RuntimeError, TimeoutError, ValueError) as exc:
        error = f"{type(exc).__name__}: {exc}"
    finally:
        try:
            for address in armed:
                rsp.command(f"z0,{address:x},4", timeout=2)
            rsp.command("D", timeout=3)
        except (ConnectionError, OSError, RuntimeError, TimeoutError, ValueError):
            pass
        sock.close()
    output.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "schema": 1,
        "experiment": "h1_runtime_callback_binding_capture",
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "emulated_process_id": pid,
        "gdb_stub": f"{HOST}:{PORT}",
        "pinned_original_code_sha256": digest,
        "installed_patch_sha256": _installed_patch_hash(),
        "breakpoints": {f"0x{a:08x}": n for a, n in BREAKPOINTS.items()},
        "events": events,
        "gate_a_callback_observed": any(x["breakpoint"] == "gate_a_callback_call" for x in events),
        "gate_b_callback_observed": any(x["breakpoint"] == "gate_b_callback_call" for x in events),
        "stopped_at_time_limit": stopped_by_timeout,
        "error": error,
        "limitations": [
            "Observations cover only this live process and the capture interval.",
            "The existing IPS changes code; its exact hash is recorded, while H1 callback entries were not patched by this capture.",
            "Breakpoint instrumentation temporarily replaces instructions and is removed before detach.",
            "A gate without a positive body/callback hit remains unobserved, not absent.",
        ],
    }
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def _installed_patch_hash() -> str | None:
    patch = Path.home() / "AppData/Roaming/Azahar/load/mods/00040000000E5C00/exefs/code.ips"
    return hashlib.sha256(patch.read_bytes()).hexdigest() if patch.is_file() else None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pid", type=lambda value: int(value, 0), default=11)
    parser.add_argument("--seconds", type=float, default=120)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.seconds <= 0:
        parser.error("--seconds must be positive")
    report = run(args.pid, args.seconds, args.output)
    print(json.dumps({"events": len(report["events"]),
                      "gate_a": report["gate_a_callback_observed"],
                      "gate_b": report["gate_b_callback_observed"],
                      "time_limit": report["stopped_at_time_limit"],
                      "error": report["error"]}, indent=2))
    return 1 if report["error"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
