#!/usr/bin/env python3
"""Paired H2 runtime with a bounded read-only nested-callback observer."""
from __future__ import annotations
import argparse, hashlib, json, shutil, socket, sys, tempfile, time, uuid
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import h2_autonomous_gdb_verify as base

CALL, CALLBACK_RET, WRAPPER_RETURN, HANDLER_RET = 0x001A07FC, 0x001A0800, 0x001A0830, 0x0019DFEC
READY, RESET = base.ADDR_TITLE_CONFIG_READY, base.ADDR_TITLE_RESET_FOR_BOOT
NESTED_TABLE, HANDLER_TABLE = 0x00406038, 0x0044DED0
WORK_GLOBAL = base.ADDR_G_TITLE_CONFIG_WORK
MAX_NESTED, MAX_HANDLERS, MAX_POLLS, MAX_SECONDS = 20, 40, 40, 120.0
PACKET = Path("build/agent-work/H2-semantic/h2-rsp-lifecycle-parity-capture/run-006/task.json")
GATE_RUNTIME = Path("build/agent-work/H2-semantic/h2-state2-nested-callback-capture/run-028/runtime-report.json")
OFFLINE = Path("build/agent-work/H2-semantic/h2-final-image-composition/run-001/checks/offline-001/report.json")
CALLER = Path("build/agent-work/H2-semantic/h2-final-image-composition/run-001/checks/offline-001/caller/report.json")
IMAGE_SHA = "acd8b2f35df08f225ca65b0fbf8aeef2dbbaa71171904e31c301e8bff6a51446"
IPS_SHA = "67e4758255fe1f4bc5877e2c997ae931613e631a5a11d487cea0e095ff630beb"
MANIFEST_SHA = "577c89588e031dc3eb1878d474cade85d5fe62f1f41c27816c4d7e92cd304d27"
CCI_SHA = "9cc760c2f37da9a4a3657e918e0eaebb3e8e80a91047e5c18f95aedf0242b4c2"

class CaptureDeadline(TimeoutError): pass

def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def _reg(rsp, n: int) -> int:
    return base.decode_r0(rsp.request(f"p{n:x}".encode("ascii")))

def _valid(addr: int, size: int = 4) -> bool:
    return 0x00100000 <= addr and addr + size <= 0x20000000

def _u32(rsp, addr: int) -> int:
    if not _valid(addr): raise base.ProbeError(f"invalid guest pointer {addr:#x}")
    return base.rsp_read_u32(rsp, addr)

def _u16(rsp, addr: int) -> int:
    if not _valid(addr, 2): raise base.ProbeError(f"invalid halfword pointer {addr:#x}")
    return int.from_bytes(base.rsp_read_mem(rsp, addr, 2), "little")

def _table(rsp, task: int, index: int) -> tuple[int, int]:
    table = _u32(rsp, task + 0xBC)
    return table, _u32(rsp, table + 4 * index)

def verify_prelaunch_gates() -> dict:
    """Hash frozen inputs and recheck the exact prelaunch gate reports."""
    packet_path = ROOT / PACKET
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    if packet.get("task", {}).get("id") != "h2-rsp-lifecycle-parity-capture":
        raise ValueError("unexpected frozen run-006 packet")
    checked = []
    for rel, expected in {**packet["input_sha256"], **packet.get("writable_baseline_sha256", {})}.items():
        path = (ROOT / rel).resolve(strict=True)
        path.relative_to(ROOT.resolve())
        actual = digest(path)
        if actual != expected: raise ValueError(f"frozen input changed: {rel}")
        checked.append({"path": rel, "sha256": actual})
    image = ROOT / "build/agent-work/H2-semantic/h2-final-image-composition/run-001/composed-003/code.h2-final.bin"
    ips = ROOT / "build/agent-work/H2-semantic/h2-final-image-composition/run-001/composed-003/code.h2-final.ips"
    manifest = ROOT / "build/agent-work/H2-semantic/h2-final-image-composition/run-001/composed-003/manifest.json"
    ih, ph, mh = digest(image), digest(ips), digest(manifest)
    if (ih, ph, mh) != (IMAGE_SHA, IPS_SHA, MANIFEST_SHA):
        raise ValueError("final image, IPS, or composition manifest pin changed")
    if base.apply_ips((ROOT / "extracted/exefs/code.bin").read_bytes(), ips.read_bytes()) != image.read_bytes():
        raise ValueError("IPS no longer composes to the pinned final image")
    offline = json.loads((ROOT / OFFLINE).read_text(encoding="utf-8"))
    caller = json.loads((ROOT / CALLER).read_text(encoding="utf-8"))
    runtime = json.loads((ROOT / GATE_RUNTIME).read_text(encoding="utf-8"))
    if offline.get("passed") is not True or offline.get("image_sha256") != ih or offline.get("manifest_sha256") != mh:
        raise ValueError("offline differential gate failed or targets a different image")
    if caller.get("passed") is not True or caller.get("production_calc_image_sha256") != ih:
        raise ValueError("caller-composition gate failed or targets a different production image")
    cci = base.DEFAULT_CCI.resolve(strict=True)
    cci_sha = digest(cci)
    if cci_sha != CCI_SHA: raise ValueError("pinned CCI hash changed")
    gates = runtime.get("offline_gates", {})
    required = ("task_input_hashes", "h2_differential", "h2_caller", "h3_final_image_caller", "arm_interworking")
    failed = {name: gates.get(name) for name in required if gates.get(name) != "passed"}
    if failed: raise ValueError(f"offline-first gates not passed: {failed}")
    return {
        "passed": True, "checked_frozen_input_count": len(checked), "input_hashes": checked,
        "image_sha256": ih, "ips_sha256": ph, "manifest_sha256": mh,
        "h2_differential": "passed", "h2_caller": "passed", "arm_interworking": "passed",
        "h3_final_image_caller": "passed",
        "retained_source_identity_warning_count": len(gates.get("h2_diff_source_identity_warnings", [])),
        "protected_user_save_read": False, "cci_path": str(cci), "cci_sha256": cci_sha,
        "report_hashes": {p.as_posix(): digest(ROOT / p) for p in (PACKET, OFFLINE, CALLER, GATE_RUNTIME)},
    }

class NestedObserver:
    """Read-only software-breakpoint observer for nested callback and readiness."""
    def __init__(self, rsp, timeout_s=MAX_SECONDS, max_nested=MAX_NESTED, max_handlers=MAX_HANDLERS):
        self.rsp, self.started = rsp, time.monotonic()
        self.deadline = self.started + timeout_s
        self.max_nested, self.max_handlers = max_nested, max_handlers
        self.nested, self.handlers, self.ready = [], [], []
        self.pending, self.active, self.caps, self.cleanup_errors = {}, set(), [], []
        self.reason, self.error, self.reset_observed = "not_started", None, False
    def _set(self, address):
        if address not in self.active:
            base.rsp_set_bp(self.rsp, address); self.active.add(address)
    def _clear(self, address):
        if address in self.active:
            base.rsp_clear_bp(self.rsp, address); self.active.discard(address)
    def arm(self):
        for address in (CALL, HANDLER_RET, READY): self._set(address)
        self.reason = "capturing"
    def close(self):
        for address in sorted(self.active, reverse=True):
            try: base.rsp_clear_bp(self.rsp, address); self.active.discard(address)
            except Exception as exc: self.cleanup_errors.append(f"{address:#x}: {exc}")
    def _continue(self):
        remaining = self.deadline - time.monotonic()
        if remaining <= 0: raise CaptureDeadline("120-second observer deadline expired")
        sock = getattr(self.rsp, "sock", None)
        previous = sock.gettimeout() if sock is not None else None
        if sock is not None: sock.settimeout(remaining if previous is None else min(previous, remaining))
        try: return self.rsp.continue_to_stop()
        except (socket.timeout, TimeoutError) as exc: raise CaptureDeadline(str(exc)) from exc
        finally:
            if sock is not None: sock.settimeout(previous)
    def _pc(self): return _reg(self.rsp, 15) & 0xffffffff
    def _nested_call(self):
        task, index, r6 = (_reg(self.rsp, n) & 0xffffffff for n in (4, 5, 6))
        method, packed = _table(self.rsp, task, index)
        hid, nid = packed & 0xffff, packed >> 16
        outer_target = _u32(self.rsp, HANDLER_TABLE + hid * 4)
        table_entry = NESTED_TABLE + nid * 8
        nested_target, actual = _u32(self.rsp, table_entry), _reg(self.rsp, 0) & 0xffffffff
        event = {
            "sequence": len(self.nested)+1, "task": hex(task), "instruction_index": index,
            "method_table": hex(method), "outer_handler_id": hid,
            "outer_handler_target_raw": hex(outer_target), "nested_id": nid,
            "nested_target_from_table_raw": hex(nested_target), "nested_target_at_blx_raw": hex(actual),
            "nested_target_matches_table": nested_target == actual, "nested_table_entry": hex(table_entry),
            "r6_table_entry": hex(r6), "blx_call_pc": hex(CALL),
            "callback_return_raw": None, "outer_handler_return_raw": None,
        }
        self.nested.append(event); self.pending.setdefault((task, index), []).append(event)
        self._clear(CALL); self._set(CALLBACK_RET)
        try:
            self.continue_until(CALLBACK_RET)
            event["callback_return_raw"] = _reg(self.rsp, 0) & 0xffffffff
            event["callback_return_pc"] = hex(CALLBACK_RET)
            work = _u32(self.rsp, WORK_GLOBAL)
            event["title_config_work"] = hex(work) if work else None
            event["title_config_state"] = _u32(self.rsp, work + 8) if work else None
        finally: self._clear(CALLBACK_RET)
        self._set(WRAPPER_RETURN)
        try:
            self.continue_until(WRAPPER_RETURN)
            event["outer_handler_return_raw"] = _reg(self.rsp, 0) & 0xffffffff
            event["outer_handler_return_pc"] = hex(WRAPPER_RETURN)
        finally:
            self._clear(WRAPPER_RETURN)
        if len(self.nested) < self.max_nested: self._set(CALL)
        elif "nested_return_cap" not in self.caps: self.caps.append("nested_return_cap")
    def _handler_return(self):
        task = _reg(self.rsp, 4) & 0xffffffff
        index = _u32(self.rsp, task + 0x18)
        method, packed = _table(self.rsp, task, index)
        hid = packed & 0xffff
        work = _u32(self.rsp, WORK_GLOBAL)
        event = {
            "sequence": len(self.handlers)+1, "task": hex(task), "instruction_index": index,
            "method_table": hex(method), "handler_id": hid,
            "handler_target_raw": hex(_u32(self.rsp, HANDLER_TABLE + 4*hid)),
            "handler_return_raw": _reg(self.rsp, 0) & 0xffffffff,
            "counter_cc": _u32(self.rsp, task + 0xCC), "counter_d0": _u32(self.rsp, task + 0xD0),
            "title_config_work": hex(work) if work else None,
            "title_config_state": _u32(self.rsp, work + 8) if work else None,
        }
        self.handlers.append(event)
        for nested in reversed(self.pending.get((task, index), [])):
            if nested["outer_handler_return_raw"] is None:
                nested["outer_handler_return_raw"] = event["handler_return_raw"]
                nested["outer_handler_return_sequence"] = event["sequence"]; break
        self._clear(HANDLER_RET)
        if len(self.handlers) < self.max_handlers: self._set(HANDLER_RET)
        elif "handler_return_cap" not in self.caps: self.caps.append("handler_return_cap")
    def continue_until(self, expected):
        while True:
            self._continue(); pc = self._pc()
            if pc == expected: return
            if pc == CALL and CALL in self.active:
                if len(self.nested) >= self.max_nested:
                    self._clear(CALL)
                    if "nested_return_cap" not in self.caps: self.caps.append("nested_return_cap")
                    continue
                self._nested_call(); continue
            if pc == HANDLER_RET and HANDLER_RET in self.active:
                if len(self.handlers) >= self.max_handlers:
                    self._clear(HANDLER_RET)
                    if "handler_return_cap" not in self.caps: self.caps.append("handler_return_cap")
                    continue
                self._handler_return(); continue
            raise base.ProbeError(f"unexpected guest stop at {pc:#x}; expected {expected:#x}")
    def run(self, max_polls=MAX_POLLS):
        if not 1 <= max_polls <= MAX_POLLS: raise ValueError("invalid readiness bound")
        try:
            self.arm()
            for frame in range(1, max_polls+1):
                self.continue_until(READY); self._clear(READY)
                work = _u32(self.rsp, WORK_GLOBAL)
                state = _u32(self.rsp, work+8) if work else None
                ret = _reg(self.rsp, 14) & 0xffffffff
                if ret & 1: ret &= ~1
                self._set(ret)
                try: self.continue_until(ret); ready = _reg(self.rsp, 0) & 0xffffffff
                finally: self._clear(ret)
                self.ready.append({"frame": frame, "work_ptr": hex(work), "work_state": state,
                                   "ready_return": ready, "return_pc": hex(ret)})
                if ready == 1:
                    self._set(RESET)
                    try: self.continue_until(RESET); self.reset_observed = True
                    finally: self._clear(RESET)
                    self.reason = "title_reset_observed"; break
                self._set(READY)
            else: self.reason = "readiness_check_cap"
        except CaptureDeadline as exc: self.reason, self.error = "wall_clock_deadline", str(exc)
        except Exception as exc: self.reason, self.error = "unexpected_stop_or_rsp_error", f"{type(exc).__name__}: {exc}"
        finally: self.close()
        return {
            "completed": bool(self.reset_observed and self.ready and self.ready[-1]["ready_return"] == 1),
            "observations": self.ready,
            "nested_callback_observation": {
                "stop_reason": self.reason, "elapsed_seconds": round(time.monotonic()-self.started, 3),
                "nested_return_count": sum(e["callback_return_raw"] is not None for e in self.nested),
                "handler_return_count": len(self.handlers), "nested_callbacks": self.nested,
                "handler_returns": self.handlers, "capture_caps": self.caps, "error": self.error,
                "breakpoints_cleared": not self.active, "cleanup_errors": self.cleanup_errors,
                "observer_guest_writes": 0,
            },
        }

def traced_wait(rsp, max_ready_checks=MAX_POLLS):
    return NestedObserver(rsp).run(max_ready_checks)

def _norm(run):
    events = run.get("post_confirm_readiness_trace", {}).get("nested_callback_observation", {}).get("nested_callbacks", [])
    keys = ("sequence", "outer_handler_id", "nested_id", "nested_target_from_table_raw",
            "nested_target_at_blx_raw", "callback_return_raw", "outer_handler_return_raw")
    return [{k: e.get(k) for k in keys} for e in events]

def compare_traces(report):
    a, b = _norm(report.get("original_run", {})), _norm(report.get("patched_run", {}))
    status = "matched_observed_events" if a and a == b else "no_events_observed" if not a and not b else "diverged_or_incomplete"
    return {"status": status, "original_event_count": len(a), "patched_event_count": len(b),
            "normalized_events_equal": a == b, "original_events": a, "patched_events": b}

def _copy_log(src, dst):
    shutil.copy2(src, dst)
    return {"path": dst.name, "bytes": dst.stat().st_size, "sha256": digest(dst)}

def _remove_temp(temp, ports, report):
    target, parent = temp.resolve(strict=True), Path(tempfile.gettempdir()).resolve(strict=True)
    if target.parent != parent or not target.name.startswith("h2cb-"):
        return {"removed": False, "reason": "staging path is not a generated h2cb temp child"}
    if any(base.listener_owner(p) is not None for p in ports):
        return {"removed": False, "reason": "GDB listener remains on a task port"}
    clean = all(report.get(s, {}).get("clean_shutdown", {}).get("clean_exit") is True
                and report.get(s, {}).get("restart_clean_shutdown", {}).get("clean_exit") is True
                and report.get(s, {}).get("listener_owner_after_first_exit") is None
                and report.get(s, {}).get("listener_owner_after_restart_exit") is None
                for s in ("original_run", "patched_run"))
    if not clean: return {"removed": False, "reason": "all clean exits/listener checks are not confirmed"}
    shutil.rmtree(target)
    return {"removed": not target.exists(), "verified_parent": str(parent), "generated_name": target.name}

def run(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if "-h" in args or "--help" in args: return base.main(args)
    parser = argparse.ArgumentParser(add_help=False); parser.add_argument("--archive-dir", type=Path, required=True)
    opts, forwarded = parser.parse_known_args(args)
    archive = opts.archive_dir if opts.archive_dir.is_absolute() else ROOT / opts.archive_dir
    archive = archive.resolve()
    output_root = (ROOT / "build/agent-work/H2-semantic/h2-postconfirm-nested-callback-trace").resolve()
    archive.relative_to(output_root)
    outp = argparse.ArgumentParser(add_help=False); outp.add_argument("--output-dir", type=Path)
    outopts, _ = outp.parse_known_args(forwarded)
    generated = outopts.output_dir is None
    if generated:
        temp = Path(tempfile.gettempdir()).resolve(strict=True) / f"h2cb-{uuid.uuid4().hex[:10]}"
        forwarded.extend(["--output-dir", str(temp)])
    else:
        temp = outopts.output_dir.resolve()
        if temp.parent != Path(tempfile.gettempdir()).resolve(strict=True) or not temp.name.startswith("h2cb-"):
            raise SystemExit("--output-dir must be a child named h2cb-* of system temp")
    report_path = temp/"autonomous-gdb-verification.json"
    attestation_path = archive/"prelaunch-gate-attestation.json"
    archived_report_path = archive/"autonomous-gdb-verification.json"
    recovery = archive.exists()
    if recovery and (not attestation_path.is_file() or archived_report_path.exists() or not report_path.is_file()):
        raise SystemExit("recovery requires an existing attestation and staged report, with no archived final report")
    gates = verify_prelaunch_gates()
    port_parser = argparse.ArgumentParser(add_help=False); port_parser.add_argument("--base-port", type=int, default=59940)
    port_opts, _ = port_parser.parse_known_args(forwarded)
    base.reserve_port(port_opts.base_port); base.reserve_port(port_opts.base_port + 1)
    gates["reserved_loopback_ports"] = [port_opts.base_port, port_opts.base_port + 1]
    if recovery:
        saved_gates = json.loads(attestation_path.read_text(encoding="utf-8"))
        if not saved_gates.get("passed") or any(saved_gates.get(k) != gates.get(k)
                for k in ("image_sha256", "ips_sha256", "manifest_sha256", "report_hashes")):
            raise SystemExit("saved prelaunch attestation does not match current frozen gates")
    else:
        archive.mkdir(parents=True)
        attestation_path.write_text(json.dumps(gates, indent=2)+"\n", encoding="utf-8")
    if report_path.exists():
        if not recovery:
            raise SystemExit("staged report exists without an authorized recovery archive")
        report = json.loads(report_path.read_text(encoding="utf-8"))
        if report.get("passed") is not True:
            raise SystemExit("staged runtime report is not a completed passing paired run")
        rc = 0
    else:
        if recovery:
            raise SystemExit("recovery report disappeared before finalization")
        prior = base.wait_for_title_reset_after_confirm
        base.wait_for_title_reset_after_confirm = traced_wait
        try: rc = base.main(forwarded)
        finally: base.wait_for_title_reset_after_confirm = prior
        if rc != 0: return rc
        report = json.loads(report_path.read_text(encoding="utf-8"))
    report["nested_callback_trace_comparison"] = compare_traces(report)
    runtime_driver_snapshot = archive.parent/"source-tools-h2_postconfirm_nested_callback_trace.py"
    runtime_driver_hash = digest(runtime_driver_snapshot) if runtime_driver_snapshot.is_file() else digest(Path(__file__).resolve())
    base_runner = ROOT/"tools/h2_autonomous_gdb_verify.py"
    report["observer_driver"] = {
        "path": "tools/h2_postconfirm_nested_callback_trace.py",
        "sha256": runtime_driver_hash,
        "runtime_source_snapshot": str(runtime_driver_snapshot.relative_to(ROOT)) if runtime_driver_snapshot.is_file() else None,
        "finalizer_path": str(Path(__file__).resolve()),
        "finalizer_sha256": digest(Path(__file__).resolve()),
        "base_runner_path": str(base_runner.resolve()), "base_runner_sha256": digest(base_runner),
        "breakpoints": [hex(CALL), hex(CALLBACK_RET), hex(WRAPPER_RETURN), hex(HANDLER_RET), hex(READY)],
        "bounds": {"nested_returns": MAX_NESTED, "handler_returns": MAX_HANDLERS,
                   "readiness_polls": MAX_POLLS, "seconds": MAX_SECONDS},
        "observer_guest_writes": 0,
        "route_limit": "The existing pre-observer route sets TitleMain selection/flag, calls UiListCursor_SetSelectedRow, and temporarily returns one-frame logical-query responses."
    }
    logs = []
    for side in ("original_run", "patched_run"):
        data = report.get(side, {})
        for key in ("stdout_path", "stderr_path"):
            src = Path(data.get(key, ""))
            if src.is_file(): logs.append(_copy_log(src, archive/f"{side.removesuffix('_run')}-{key.removesuffix('_path')}.log"))
        app = Path(data.get("staged_executable_path", "")).parent
        for src in (app/"azahar_log.txt", app/"user"/"azahar_log.txt",
                    app/"user"/"log"/"azahar_log.txt", app/"user"/"log"/"azahar_log.old.txt"):
            if src.is_file():
                suffix = "azahar_log_old" if src.name.endswith(".old.txt") else "azahar_log"
                logs.append(_copy_log(src, archive/f"{side.removesuffix('_run')}-{suffix}.txt"))
    report["archived_logs"] = logs
    cleanup = _remove_temp(temp, (report["base_port"], report["base_port"]+1), report)
    report["temporary_staging_cleanup"] = cleanup
    if (generated or recovery) and not cleanup["removed"]: report["temporary_staging_cleanup"]["generated_temp_root"] = str(temp)
    (archive/"autonomous-gdb-verification.json").write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({"exit_code": rc, "report": str(archive/"autonomous-gdb-verification.json"),
                      "nested_callback_trace_comparison": report["nested_callback_trace_comparison"],
                      "temporary_staging_cleanup": cleanup}, indent=2))
    return rc

if __name__ == "__main__":
    raise SystemExit(run())
