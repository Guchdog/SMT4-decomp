#!/usr/bin/env python3
"""Autonomous paired getter observation over loopback Azahar GDB RSP.

Default mode performs offline image and interworking checks only. Runtime launch
requires explicit --launch; no input is synthesized beyond the existing one-shot
start-screen bypass from the H2 harness. Missing getter hits are inconclusive.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.h2_azahar_rsp_probe import ProbeError, Rsp, listener_owner, reserve_port, sha256
from tools.h2_autonomous_gdb_verify import (
    DEFAULT_CCI, DEFAULT_DLL_SOURCE, DEFAULT_PRIVATE_EXE, DEFAULT_SEED,
    ADDR_TITLE_MAIN_INIT, ADDR_UI_INPUT_TRIGGER2, rsp_read_mem, rsp_set_bp,
    rsp_clear_bp, stage_portable_dir,
)
from tools.h18_script_getters_stage import _apply_ips, TEXT
from tools.h18_script_word_getters_production import CALLER_PAIRS, verify_reference

GETTERS = (0x002345F0, 0x002345FC)
DEFAULT_ORIGINAL = ROOT / "extracted/exefs/code.bin"
DEFAULT_IPS = ROOT / "build/agent-work/batch-h18-001/h18-getters-stage/run-001/checks/staged-validation/stage/getters-patched.code.ips"
DEFAULT_OFFLINE_REPORTS = (
    ROOT / "build/agent-work/batch-h18-001/h18-getters-stage/run-001/checks/staged-validation/seed-7/report.json",
    ROOT / "build/agent-work/batch-h18-001/h18-getters-stage/run-001/checks/staged-validation/seed-20261024/report.json",
)
EXPECTED_OFFLINE_REPORT_HASHES = (
    "409406c385178aea44a3454d54fea462995805e109a9a55093f33c855010f735",
    "e6c7d359085fa3c08aef89bf748fea1b280a85ebec299e4f5e72c826af24b88a",
)


def u32(rsp: Rsp, reg: int) -> int:
    raw = rsp.request(f"p{reg:02x}".encode("ascii"))
    if raw.startswith(b"E") or len(raw) != 8:
        raise ProbeError(f"register read p{reg:02x} failed: {raw!r}")
    return int.from_bytes(bytes.fromhex(raw.decode("ascii")), "little")


def cpsr(rsp: Rsp) -> int:
    return u32(rsp, 25)  # GDB ARM register 25 is CPSR in the target register file.


def verify_patch(original_path: Path, ips_path: Path) -> dict:
    original = original_path.read_bytes()
    ips = ips_path.read_bytes()
    patched = _apply_ips(original, ips)
    changes = [i for i, (a, b) in enumerate(zip(original, patched)) if a != b]
    allowed = {i for addr in GETTERS for i in range(addr - TEXT, addr - TEXT + 8)}
    if not set(changes).issubset(allowed):
        raise ValueError(f"IPS changed bytes outside getter bodies: {sorted(set(changes) - allowed)[:8]}")
    expected_bodies = {GETTERS[0]: bytes.fromhex("4800d0e51eff2fe1"),
                       GETTERS[1]: bytes.fromhex("4a00d0e51eff2fe1")}
    for addr, body in expected_bodies.items():
        if patched[addr-TEXT:addr-TEXT+8] != body:
            raise ValueError(f"unexpected patched ARM body at {addr:#x}")
    inventory = verify_reference(original_path, ROOT / "config/game_info.json", ROOT / "config/functions.csv")
    branch_counts = {}
    for addr in GETTERS:
        key = hex(addr).lower()
        refs = inventory["external_references"][key]["branches"]
        if len(refs) != 16 or inventory["external_references"][key]["pointer_words"]:
            raise ValueError(f"unexpected direct caller inventory for {key}: {inventory['external_references'][key]}")
        branch_counts[key] = len(refs)
        for ref in refs:
            site, target = int(ref["site"], 16), int(ref["target"], 16)
            if target != addr or target & 1:
                raise ValueError(f"caller {site:#x} has wrong/non-ARM BL target {target:#x}")
            if original[site-TEXT:site-TEXT+4] != patched[site-TEXT:site-TEXT+4]:
                raise ValueError(f"IPS unexpectedly modified caller instruction at {site:#x}")
    for addr in GETTERS:
        if addr & 1:
            raise ValueError(f"getter address carries Thumb bit: {addr:#x}")
    return {"original_sha256": hashlib.sha256(original).hexdigest(),
            "ips_sha256": hashlib.sha256(ips).hexdigest(),
            "patched_sha256": hashlib.sha256(patched).hexdigest(),
            "changed_byte_count": len(changes), "changed_ranges": [
                {"address": hex(addr), "file_offset": hex(addr-TEXT), "size": 8} for addr in GETTERS],
            "caller_functions_instrumented": [x["caller"] for x in CALLER_PAIRS],
            "direct_arm_bl_counts": branch_counts,
            "arm_entry_addresses_even": True, "interworking": "all specified getter entries and checked BL targets are ARM-state even addresses"}



def verify_offline_reports(paths: tuple[Path, ...], patch: dict) -> list[dict]:
    if len(paths) != 2:
        raise ValueError("offline gate requires the two pinned seed reports")
    expected_seeds = (7, 20261024)
    output = []
    for path, expected_hash, seed in zip(paths, EXPECTED_OFFLINE_REPORT_HASHES, expected_seeds):
        digest = sha256(path)
        if digest != expected_hash:
            raise ValueError(f"offline report provenance hash mismatch: {path}")
        report = json.loads(path.read_text(encoding="utf-8"))
        if report.get("seed") != seed or not report.get("passed"):
            raise ValueError(f"offline differential did not pass for seed {seed}")
        if report.get("reference_sha256") != patch["original_sha256"] or report.get("patched_image_sha256") != patch["patched_sha256"] or report.get("ips_sha256") != patch["ips_sha256"]:
            raise ValueError(f"offline report image/IPS provenance mismatch for seed {seed}")
        if not all(row.get("passed") and row.get("cases") == 80 for row in report.get("functions", [])) or len(report.get("functions", [])) != 2:
            raise ValueError(f"offline getter differential coverage incomplete for seed {seed}")
        if len(report.get("caller_windows", [])) != 4 or not all(row.get("passed") for row in report["caller_windows"]):
            raise ValueError(f"offline caller composition incomplete for seed {seed}")
        if len(report.get("negative_controls", [])) != 2 or not all(row.get("detected") for row in report["negative_controls"]):
            raise ValueError(f"offline negative controls did not detect mutants for seed {seed}")
        output.append({"path": path.as_posix(), "sha256": digest, "seed": seed,
                       "functions": 2, "cases_per_function": 80, "caller_windows": 4,
                       "negative_controls_detected": 2, "passed": True})
    return output


def read_regs(rsp: Rsp) -> dict:
    values = {f"r{i}": u32(rsp, i) for i in range(13)}
    values.update(sp=u32(rsp, 13), lr=u32(rsp, 14), pc=u32(rsp, 15), cpsr=cpsr(rsp))
    return values


def getter_bytes(rsp: Rsp, pointer: int) -> bytes | None:
    if pointer == 0 or pointer > 0xFFFFFFB7:
        return None
    try:
        return rsp_read_mem(rsp, pointer + 0x48, 4)
    except Exception:
        return None


def capture_one(rsp: Rsp, addr: int, ordinal: int, profile: str) -> dict:
    rsp_clear_bp(rsp, addr)
    entry = read_regs(rsp)
    lr = entry["lr"]
    if lr & 1:
        raise ProbeError(f"unexpected Thumb continuation LR={lr:#x}; this inventory is ARM BL-only")
    observed_bytes = getter_bytes(rsp, entry["r0"])
    record = {"profile": profile, "getter": hex(addr), "ordinal": ordinal,
              "entry_pc": hex(entry["pc"]), "caller": hex((lr - 4) & 0xFFFFFFFF),
              "return_pc": hex(lr), "input_pointer": hex(entry["r0"]),
              "input_bytes_0x48_0x4b": None if observed_bytes is None else observed_bytes.hex(),
              "entry_cpsr": hex(entry["cpsr"]),
              "callee_saved_entry": {k: hex(entry[k]) for k in ("r4","r5","r6","r7","r8","r9","r10","r11","sp")}}
    rsp_set_bp(rsp, lr)
    reply = rsp.continue_to_stop()
    ret = read_regs(rsp)
    rsp_clear_bp(rsp, lr)
    record.update({"stop_reply": reply.decode("ascii", "replace"), "return_pc": hex(ret["pc"]),
                   "returned_r0": hex(ret["r0"]), "return_cpsr": hex(ret["cpsr"]),
                   "callee_saved_return": {k: hex(ret[k]) for k in ("r4","r5","r6","r7","r8","r9","r10","r11","sp","lr")},
                   "return_input_bytes_0x48_0x4b": None if (observed_bytes := getter_bytes(rsp, entry["r0"])) is None else observed_bytes.hex()})
    rsp_set_bp(rsp, addr)
    return record


def hidden_popen(command: list[str], cwd: Path, out, err):
    kwargs = dict(cwd=str(cwd), stdin=subprocess.DEVNULL, stdout=out, stderr=err, shell=False)
    if os.name == "nt":
        startup = subprocess.STARTUPINFO()
        startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startup.wShowWindow = 0
        kwargs["startupinfo"] = startup
    return subprocess.Popen(command, **kwargs)


def run_profile(exe: Path, cci: Path, port: int, profile: str, timeout: float,
                max_events: int) -> dict:
    reserve_port(port)
    root = exe.parent.parent
    out_path, err_path = root / "azahar.stdout.log", root / "azahar.stderr.log"
    counts = {addr: 0 for addr in GETTERS}
    events = []
    launch = [str(exe), "-g", str(port), str(cci)]
    with out_path.open("w", encoding="utf-8") as out, err_path.open("w", encoding="utf-8") as err:
        proc = hidden_popen(launch, exe.parent, out, err)
        sock = None
        try:
            deadline = time.monotonic() + min(timeout, 60)
            while time.monotonic() < deadline:
                if proc.poll() is not None:
                    raise ProbeError(f"Azahar exited before RSP attach: {proc.returncode}")
                owner = listener_owner(port)
                if owner is not None:
                    break
                time.sleep(.2)
            if listener_owner(port) != proc.pid:
                raise ProbeError(f"GDB listener {port} is not owned by isolated process {proc.pid}")
            sock = socket.create_connection(("127.0.0.1", port), timeout=timeout)
            rsp = Rsp(sock, timeout=timeout)
            supported = rsp.request(b"qSupported:multiprocess+;swbreak+;hwbreak+")
            if not supported or supported.startswith(b"E") or rsp.request(b"!") != b"OK":
                raise ProbeError("GDB RSP handshake failed")
            proc_info = rsp.request(b"qfProcessInfo")
            if not proc_info.startswith(b"pid:"):
                raise ProbeError(f"process discovery failed: {proc_info!r}")
            pid = proc_info.split(b":",1)[1].split(b";",1)[0]
            if not rsp.request(b"vAttach;" + pid).startswith(b"T"):
                raise ProbeError("GDB attach failed")
            old_trigger = rsp_read_mem(rsp, ADDR_UI_INPUT_TRIGGER2, 8)
            rsp_set_bp(rsp, ADDR_TITLE_MAIN_INIT)
            for addr in GETTERS: rsp_set_bp(rsp, addr)
            write_stub = b"M" + f"{ADDR_UI_INPUT_TRIGGER2:x},8:".encode() + bytes.fromhex("0100a0e31eff2fe1").hex().encode()
            if rsp.request(write_stub) != b"OK": raise ProbeError("failed to install start input helper")
            try:
                rsp.sock.settimeout(timeout)
                start_reached = False
                startup_timed_out = False
                while len(events) < max_events:
                    try:
                        reply = rsp.continue_to_stop()
                    except (TimeoutError, socket.timeout):
                        startup_timed_out = True
                        break
                    pc = u32(rsp, 15)
                    if pc == ADDR_TITLE_MAIN_INIT:
                        rsp_clear_bp(rsp, ADDR_TITLE_MAIN_INIT)
                        rsp_write = b"M" + f"{ADDR_UI_INPUT_TRIGGER2:x},8:".encode() + old_trigger.hex().encode()
                        if rsp.request(rsp_write) != b"OK": raise ProbeError("failed to restore start input helper")
                        start_reached = True
                        break
                    match = next((a for a in GETTERS if pc == a), None)
                    if match is None:
                        raise ProbeError(f"unexpected stop while waiting for getter/title init: pc={pc:#x} reply={reply!r}")
                    counts[match] += 1
                    events.append(capture_one(rsp, match, counts[match], profile))
                while start_reached and len(events) < max_events:
                    try:
                        reply = rsp.continue_to_stop()
                    except (TimeoutError, socket.timeout):
                        break
                    pc = u32(rsp, 15)
                    match = next((a for a in GETTERS if pc == a), None)
                    if match is None:
                        raise ProbeError(f"unexpected debugger stop: pc={pc:#x}, reply={reply!r}")
                    counts[match] += 1
                    events.append(capture_one(rsp, match, counts[match], profile))
            finally:
                # Restore the temporary input hook even on failure.
                try: rsp.request(b"M" + f"{ADDR_UI_INPUT_TRIGGER2:x},8:".encode() + old_trigger.hex().encode())
                except Exception: pass
            return {"profile": profile, "launch_argv": launch, "host_pid": proc.pid,
                    "gdb_port": port, "title_main_init_reached": start_reached,
                    "startup_timed_out": startup_timed_out,
                    "getter_hit_counts": {hex(k): v for k,v in counts.items()},
                    "events": events, "no_hit_inconclusive": not events}
        finally:
            if sock: sock.close()
            if proc.poll() is None:
                proc.terminate()
                try: proc.wait(timeout=8)
                except subprocess.TimeoutExpired:
                    proc.kill(); proc.wait(timeout=5)


def compare(original: dict, patched: dict) -> dict:
    def normalized(run):
        # Heap input pointers may vary; compare their observed bytes, return values,
        # calling locations, ordinals, continuations, flags and callee-saved state.
        return [{k:e.get(k) for k in ("getter","ordinal","caller","input_bytes_0x48_0x4b",
                "return_pc","returned_r0","entry_cpsr","return_cpsr","callee_saved_entry","callee_saved_return")}
                for e in run["events"]]
    has_hits = bool(original["events"] and patched["events"])
    scenarios_complete = original["title_main_init_reached"] and patched["title_main_init_reached"]
    equal = has_hits and scenarios_complete and normalized(original) == normalized(patched)
    status = "matched" if equal else ("inconclusive_no_hits" if not has_hits else ("inconclusive_scenario_incomplete" if not scenarios_complete else "mismatch"))
    return {"status": status,
            "normalized_event_sequences_equal": equal,
            "original_hits": len(original["events"]), "patched_hits": len(patched["events"]),
            "original_hit_counts": original["getter_hit_counts"], "patched_hit_counts": patched["getter_hit_counts"],
            "note": "No getter hit or incomplete scripted start in either paired run is inconclusive, never a pass."}


def main(argv=None) -> int:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--original-code",type=Path,default=DEFAULT_ORIGINAL)
    ap.add_argument("--ips",type=Path,default=DEFAULT_IPS)
    ap.add_argument("--offline-report",type=Path,action="append",help="seed report; provide both frozen reports to override defaults")
    ap.add_argument("--azahar",type=Path,default=DEFAULT_PRIVATE_EXE)
    ap.add_argument("--dll-source",type=Path,default=DEFAULT_DLL_SOURCE)
    ap.add_argument("--game",type=Path,default=DEFAULT_CCI)
    ap.add_argument("--profile-seed",type=Path,default=DEFAULT_SEED)
    ap.add_argument("--output-dir",type=Path,required=True)
    ap.add_argument("--base-port",type=int,default=59962)
    ap.add_argument("--timeout",type=float,default=45.0)
    ap.add_argument("--max-events",type=int,default=5000)
    ap.add_argument("--check-only",action="store_true",help="offline image/interworking check; never launches emulator")
    ap.add_argument("--launch",action="store_true",help="explicitly launch paired original/patched runtime sessions")
    a=ap.parse_args(argv)
    verified=verify_patch(a.original_code,a.ips)
    offline_reports=tuple(a.offline_report) if a.offline_report else DEFAULT_OFFLINE_REPORTS
    offline_gate=verify_offline_reports(offline_reports, verified)
    if not a.launch:
        if not a.check_only:
            print(json.dumps({"offline_checks":"passed","launch_required":True,"patch":verified},indent=2))
            return 2
        if a.output_dir.exists(): raise SystemExit(f"output must be fresh: {a.output_dir}")
        a.output_dir.mkdir(parents=True)
        report={"offline_checks":"passed","launch_required":True,"patch":verified,"offline_gate":offline_gate,
                "emulator_launched":False,"timestamp_utc":datetime.now(timezone.utc).isoformat()}
        report_path=a.output_dir/"offline-check.json"
        report_path.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
        print(json.dumps({"report":str(report_path.resolve()),"offline_checks":"passed"},indent=2))
        return 0
    if a.output_dir.exists(): raise SystemExit(f"output must be fresh: {a.output_dir}")
    out=a.output_dir.resolve(); out.mkdir(parents=True)
    for p in (a.azahar,a.dll_source,a.game,a.profile_seed): p.resolve(strict=True)
    orig_exe,orig_cci=stage_portable_dir(a.azahar.resolve(),a.dll_source.resolve(),a.game.resolve(),a.profile_seed.resolve(),out/"original",None)
    patched_exe,patched_cci=stage_portable_dir(a.azahar.resolve(),a.dll_source.resolve(),a.game.resolve(),a.profile_seed.resolve(),out/"patched",a.ips.read_bytes())
    private_before=sha256(a.azahar)
    game_before=sha256(a.game)
    seed_before=[{"path":x.relative_to(a.profile_seed).as_posix(),"sha256":sha256(x)}
                 for x in sorted(a.profile_seed.rglob("*")) if x.is_file()]
    original=run_profile(orig_exe,orig_cci,a.base_port,"original",a.timeout,a.max_events)
    patched=run_profile(patched_exe,patched_cci,a.base_port+1,"patched",a.timeout,a.max_events)
    private_after=sha256(a.azahar)
    game_after=sha256(a.game)
    seed_after=[{"path":x.relative_to(a.profile_seed).as_posix(),"sha256":sha256(x)}
                for x in sorted(a.profile_seed.rglob("*")) if x.is_file()]
    report={"schema_version":1,"timestamp_utc":datetime.now(timezone.utc).isoformat(),
            "patch_validation":verified,"offline_gate":offline_gate,"private_azahar_sha256_before":private_before,"private_azahar_sha256_after":private_after,
            "game_sha256_before":game_before,"game_sha256_after":game_after,
            "profile_seed_files_before":seed_before,"profile_seed_files_after":seed_after,
            "external_inputs_unchanged":private_before==private_after and game_before==game_after and seed_before==seed_after,
            "original":original,"patched":patched,"comparison":compare(original,patched),
            "limitations":["Only getter calls in this scripted startup/title-idle route are observed; no deterministic script VM trigger is known.",
              "No-hit outcome is inconclusive.","GDB RAM reads do not establish MMIO, read-width-sensitive, fault-boundary or race equivalence."]}
    if not report["external_inputs_unchanged"]:
        report["comparison"]["status"]="input_mutated"
    (out/"getter-runtime-report.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"report":str(out/"getter-runtime-report.json"),"status":report['comparison']['status']}))
    return 0 if report["comparison"]["status"]=="matched" and report["external_inputs_unchanged"] else 1

if __name__=="__main__": raise SystemExit(main())
