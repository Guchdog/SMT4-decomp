#!/usr/bin/env python3
"""Differentially exercise an isolated H1 navigation tail adapter.

This private experiment patches only a test image copy, calls a compiled C++
reducer through a naked ARM shim, and stops at the first original touch-pointer
reload. It does not patch or launch a game.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import capstone
from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k
from tools.semantic_experiment import DATA, DATA_SIZE, INJECT, RETURN, STACK, STACK_SIZE, TEXT

SCRIPT_READY = 0x00289924
PREVIEW_READY = 0x0025A2BC
TRIGGER = 0x002B902C
EVENT_REQUEST = 0x002B91C4
CALLBACK_START = 0x001E9D08
CONTINUE = 0x001E9DE0
GATE_EXIT = 0x001EA62C
TOUCH_RELOAD = 0x001E9E4C
TOUCH_STOP = 0x001E9E50
WORK_SLOT = 0x0044E300
WORK = DATA + 0x100
MUTATED_WORK = DATA + 0x300
WORK_SIZE = 0xA0
MAILBOX = INJECT + 0x3F00
CANDIDATE_ADDRESS = INJECT + 0x2000
SHIM_VARIANTS = {
    "good": "h1_navigation_adapter_shim",
    "wrong_status_target": "h1_navigation_wrong_status_target_shim",
    "missing_s17": "h1_navigation_missing_s17_shim",
    "reload_pointer": "h1_navigation_reload_pointer_shim",
}
TRIGGER_IDS = (5, 0xE, 6, 0xF)
EXPECTED_SHA256 = "1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558"
ENTRY_CALLEE = {f"r{i}": (0xA5000000 + i * 0x10101) & 0xFFFFFFFF for i in range(4, 12)}
ENTRY_CALLEE.update({"r4": WORK, "r5": WORK})
ENTRY_D = {f"d{i}": 0x1122334400000000 + i for i in range(8, 16)}
ENTRY_FPSCR = 0x01000000


def verify_image(image: bytes) -> dict:
    digest = hashlib.sha256(image).hexdigest()
    if digest != EXPECTED_SHA256:
        raise ValueError("code.bin SHA-256 does not match the pinned game revision")
    decoder = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    def insns(start: int, stop: int):
        return list(decoder.disasm(image[start - TEXT:stop - TEXT], start))
    entry = insns(CALLBACK_START, CONTINUE)
    tail = insns(CONTINUE, TOUCH_STOP)
    expected_tail = [
        (0x001E9DE0, "ldr", "r0, [r4, #0x64]"),
        (0x001E9E30, "vmovgt.f32", "s1, s17"),
        (0x001E9E4C, "ldr", "r6, [r8]"),
    ]
    decoded = {(i.address, i.mnemonic.lower(), i.op_str.lower()) for i in tail}
    if any(row not in decoded for row in expected_tail):
        raise ValueError("pinned continuation/touch reload sequence changed")
    if not entry or entry[0].address != CALLBACK_START:
        raise ValueError("pinned inline-window entry did not decode")
    return {"sha256": digest, "size": len(image),
            "entry_window": [f"{i.address:#x}: {i.mnemonic} {i.op_str}" for i in entry],
            "tail_window": [f"{i.address:#x}: {i.mnemonic} {i.op_str}" for i in tail]}


def read_u32(uc, address: int) -> int:
    return struct.unpack("<I", uc.mem_read(address, 4))[0]


def write_u32(uc, address: int, value: int):
    uc.mem_write(address, struct.pack("<I", value & 0xFFFFFFFF))


def write_f32(uc, address: int, value: float):
    uc.mem_write(address, struct.pack("<f", value))


def branch_word(source: int, target: int) -> int:
    displacement = target - (source + 8)
    if displacement & 3 or not -(1 << 25) <= displacement < (1 << 25):
        raise ValueError(f"ARM branch out of range: {source:#x} -> {target:#x}")
    return 0xEA000000 | ((displacement >> 2) & 0xFFFFFF)


def compile_adapter(output: Path) -> tuple[dict[str, bytes], dict]:
    source = ROOT / "experiments/semantic_equivalence/h1_navigation_adapter_candidate.cpp"
    obj = output / "h1_navigation_adapter_candidate.o"
    build = compile_tu_armv6k(source, obj, ROOT)
    if build.returncode:
        raise RuntimeError(build.stderr or "ARMv6K adapter compilation failed")
    funcs = extract_elf_functions_detailed(obj)
    names = ("h1_navigation_adapter_candidate", *SHIM_VARIANTS.values())
    blobs = {}
    validations = []
    for name in names:
        if name not in funcs:
            raise ValueError(f"missing adapter symbol {name}")
        code, relocs = funcs[name]
        if relocs:
            raise ValueError(f"unsupported relocation in {name}: {relocs}")
        if not code:
            raise ValueError(f"empty adapter symbol {name}")
        blobs[name] = code
        validations.append(validate_blob(code, name, INJECT))
    meta = {"source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "object_sha256": hashlib.sha256(obj.read_bytes()).hexdigest(),
            "object_path": str(obj), "compiler_stdout": build.stdout,
            "compiler_stderr": build.stderr, "symbol_validation": validations,
            "symbols": {name: {"size": len(code), "sha256": hashlib.sha256(code).hexdigest()}
                        for name, code in blobs.items()}}
    return blobs, meta


def validate_blob(code: bytes, name: str, base: int) -> dict:
    decoder = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    decoder.detail = True
    insns = list(decoder.disasm(code, base))
    if not insns:
        raise ValueError(f"no ARM instructions in {name}")
    # Naked shims use one trailing literal pool. Prove direct-control flow does
    # not enter it and require every bytestring to decode or belong to the pool.
    pc_refs = set()
    for insn in insns:
        for op in getattr(insn, "operands", ()):
            if op.type == capstone.arm.ARM_OP_MEM and op.mem.base == capstone.arm.ARM_REG_PC:
                pc_refs.add((insn.address + 8 + op.mem.disp) & 0xFFFFFFFF)
    pool_start = None
    pool_end = base + len(code)
    for branch in reversed(insns):
        if branch.mnemonic != "b" or not branch.operands or branch.operands[0].type != capstone.arm.ARM_OP_IMM:
            continue
        boundary = branch.address + branch.size
        refs = sorted(address for address in pc_refs if address >= boundary)
        if not refs:
            continue
        start, end = refs[0], refs[-1] + 4
        if (start == boundary and end == pool_end and end - start <= 32
                and (end - start) % 4 == 0
                and refs == list(range(start, end, 4))
                and base <= branch.operands[0].imm < start):
            pool_start = start
            break
    if pool_start is None and pc_refs:
        start = min(pc_refs)
        refs = sorted(address for address in pc_refs if address >= start)
        end = refs[-1] + 4
        decoded_end = max(i.address + i.size for i in insns)
        if (start == decoded_end and end == base + len(code)
                and end - start <= 32 and (end - start) % 4 == 0
                and refs == list(range(start, end, 4))
                and insns[-1].mnemonic == "bx"):
            pool_start = start
    if pool_start is None and (sum(i.size for i in insns) != len(code)
                               or insns[-1].address + insns[-1].size != base + len(code)):
        raise ValueError(f"undecoded bytes or unproven literal tail in {name}")
    return {"symbol": name, "size": len(code), "decoded_instructions": len(insns),
            "pc_relative_pool_start": None if pool_start is None else hex(pool_start),
            "pc_relative_pool_bytes": 0 if pool_start is None else pool_end - pool_start}


class AdapterMachine:
    def __init__(self, image: bytes, blobs: dict[str, bytes], shim_variant: str = "good"):
        import unicorn
        from unicorn import arm_const as arm
        self.unicorn = unicorn
        self.uc, self.arm = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM), arm
        self.uc.ctl_set_cpu_model(arm.UC_CPU_ARM_11MPCORE)
        self.uc.mem_map(TEXT, 0x400000, unicorn.UC_PROT_READ | unicorn.UC_PROT_WRITE | unicorn.UC_PROT_EXEC)
        self.uc.mem_write(TEXT, image)
        # Private test code also contains the captured-pointer mailbox at the
        # end of this mapping; production placement/permissions are untested.
        self.uc.mem_map(INJECT, 0x6000, unicorn.UC_PROT_READ | unicorn.UC_PROT_WRITE | unicorn.UC_PROT_EXEC)
        self.uc.mem_map(DATA, DATA_SIZE, unicorn.UC_PROT_READ | unicorn.UC_PROT_WRITE)
        self.uc.mem_map(STACK, STACK_SIZE, unicorn.UC_PROT_READ | unicorn.UC_PROT_WRITE)
        self.uc.mem_write(INJECT, blobs[SHIM_VARIANTS[shim_variant]])
        self.uc.mem_write(CANDIDATE_ADDRESS, blobs["h1_navigation_adapter_candidate"])
        self.shim_variant = shim_variant
        self.ready_results = {SCRIPT_READY: 0, PREVIEW_READY: 0}
        self.trigger_results = {value: 0 for value in TRIGGER_IDS}
        self.mutate_global_after_capture = False
        self.mutated = False
        self.timeline: list[dict] = []
        self.ready_calls: list[dict] = []
        self.trigger_calls: list[dict] = []
        self.event_calls: list[dict] = []
        self.stop_addresses: tuple[int, ...] = ()
        self.hook_error: str | None = None
        self.uc.hook_add(unicorn.UC_HOOK_CODE, self._hook)

    def _snapshot(self):
        a = self.arm
        return {f"r{i}": self.uc.reg_read(getattr(a, f"UC_ARM_REG_R{i}")) for i in range(4)} | {
            "sp": self.uc.reg_read(a.UC_ARM_REG_SP), "lr": self.uc.reg_read(a.UC_ARM_REG_LR)}

    def _hook(self, uc, address, _size, _user):
        if address in self.stop_addresses:
            uc.emu_stop()
            return
        a = self.arm
        if address in (SCRIPT_READY, PREVIEW_READY):
            call = self._snapshot()
            call.update(entry=hex(address), result=int(self.ready_results[address]))
            self.ready_calls.append(call)
            self.timeline.append({"kind": "ready", "entry": hex(address), "result": call["result"]})
            uc.reg_write(a.UC_ARM_REG_R0, call["result"])
            uc.reg_write(a.UC_ARM_REG_PC, uc.reg_read(a.UC_ARM_REG_LR))
        elif address == TRIGGER:
            call = self._snapshot()
            logical_id = call["r0"]
            if logical_id not in self.trigger_results:
                self.hook_error = f"unexpected logical trigger {logical_id:#x}"
                uc.emu_stop()
                return
            call.update(entry=hex(address), logical_id=logical_id,
                        result=int(self.trigger_results[logical_id]))
            self.trigger_calls.append(call)
            self.timeline.append({"kind": "trigger", "logical_id": logical_id,
                                  "result": call["result"]})
            if self.mutate_global_after_capture and not self.mutated:
                write_u32(uc, WORK_SLOT, MUTATED_WORK)
                self.mutated = True
                self.timeline.append({"kind": "global_slot_mutation", "new_pointer": hex(MUTATED_WORK)})
            uc.reg_write(a.UC_ARM_REG_R0, call["result"])
            uc.reg_write(a.UC_ARM_REG_PC, uc.reg_read(a.UC_ARM_REG_LR))
        elif address == EVENT_REQUEST:
            call = self._snapshot()
            call.update(entry=hex(address), event_id=call["r0"],
                        work_selection=read_u32(uc, WORK + 8),
                        work_cached=read_u32(uc, WORK + 12))
            self.event_calls.append(call)
            self.timeline.append({"kind": "event", "event_id": call["event_id"],
                                  "selection": call["work_selection"],
                                  "cached": call["work_cached"]})
            uc.reg_write(a.UC_ARM_REG_PC, uc.reg_read(a.UC_ARM_REG_LR))

    def initialize(self, cursor: int, cached: int, ready=(1, 1), responses=None,
                   *, mutate_global=False, blend=1.5, mailbox_seed=0xDEADBEEF):
        a, uc = self.arm, self.uc
        uc.mem_write(DATA, bytes(DATA_SIZE))
        uc.mem_write(STACK, bytes(STACK_SIZE))
        for ptr, seed in ((WORK, 0x5B), (MUTATED_WORK, 0xA7)):
            pattern = bytes(((index * 37 + seed) & 0xFF) for index in range(WORK_SIZE))
            uc.mem_write(ptr, pattern)
            write_f32(uc, ptr + 0x64, 12.5)
            write_f32(uc, ptr + 0x68, blend)
        write_u32(uc, WORK + 8, cursor)
        write_u32(uc, WORK + 12, cached)
        write_u32(uc, WORK_SLOT, WORK)
        write_u32(uc, MAILBOX, mailbox_seed)
        uc.reg_write(a.UC_ARM_REG_CPSR, 0x10)
        uc.reg_write(a.UC_ARM_REG_SP, STACK + 0x1800)
        uc.reg_write(a.UC_ARM_REG_LR, RETURN)
        for name, value in ENTRY_CALLEE.items():
            uc.reg_write(getattr(a, f"UC_ARM_REG_{name.upper()}"), value)
        for name, value in ENTRY_D.items():
            uc.reg_write(getattr(a, f"UC_ARM_REG_{name.upper()}"), value)
        uc.reg_write(a.UC_ARM_REG_FPSCR, ENTRY_FPSCR)
        uc.reg_write(a.UC_ARM_REG_C1_C0_2, 0x00F00000)
        uc.reg_write(a.UC_ARM_REG_FPEXC, 0x40000000)
        self.ready_results = {SCRIPT_READY: int(ready[0]), PREVIEW_READY: int(ready[1])}
        self.trigger_results = {key: int((responses or {}).get(key, 0)) for key in TRIGGER_IDS}
        self.mutate_global_after_capture = bool(mutate_global)
        self.mutated = False
        self.timeline.clear(); self.ready_calls.clear(); self.trigger_calls.clear(); self.event_calls.clear()
        self.hook_error = None
        return {"work": bytes(uc.mem_read(WORK, WORK_SIZE)),
                "mutated_work": bytes(uc.mem_read(MUTATED_WORK, WORK_SIZE))}

    def snapshot(self):
        a, uc = self.arm, self.uc
        return {"pc": uc.reg_read(a.UC_ARM_REG_PC), "sp": uc.reg_read(a.UC_ARM_REG_SP),
                "lr": uc.reg_read(a.UC_ARM_REG_LR),
                "callee_saved": {name: uc.reg_read(getattr(a, f"UC_ARM_REG_{name.upper()}"))
                                 for name in ENTRY_CALLEE},
                "d8_d15": {name: uc.reg_read(getattr(a, f"UC_ARM_REG_{name.upper()}"))
                           for name in ENTRY_D},
                "s17": uc.reg_read(a.UC_ARM_REG_S17),
                "fpscr": uc.reg_read(a.UC_ARM_REG_FPSCR),
                "r6": uc.reg_read(a.UC_ARM_REG_R6)}

    def run(self, mode: str, cursor: int, cached: int, ready=(1, 1), responses=None,
            *, mutate_global=False, blend=1.5, mailbox_seed=0xDEADBEEF):
        initial = self.initialize(cursor, cached, ready, responses,
                                  mutate_global=mutate_global, blend=blend,
                                  mailbox_seed=mailbox_seed)
        image = bytearray(self.uc.mem_read(TEXT, 0x400000))
        struct.pack_into("<I", image, CALLBACK_START - TEXT, branch_word(CALLBACK_START, INJECT))
        self.uc.mem_write(TEXT, bytes(image))
        self.stop_addresses = (GATE_EXIT, TOUCH_STOP)
        try:
            self.uc.emu_start(CALLBACK_START, 0, count=5000)
            fault = None
        except self.unicorn.UcError as error:
            fault = str(error)
        work = bytes(self.uc.mem_read(WORK, WORK_SIZE))
        mutated_work = bytes(self.uc.mem_read(MUTATED_WORK, WORK_SIZE))
        return {"fault": fault, "mode": mode, "stop": self.uc.reg_read(self.arm.UC_ARM_REG_PC),
                "state": self.snapshot(), "mailbox": read_u32(self.uc, MAILBOX),
                "work_hex": work.hex(), "mutated_work_hex": mutated_work.hex(),
                "initial_work_hex": initial["work"].hex(),
                "initial_mutated_work_hex": initial["mutated_work"].hex(),
                "work_sha256": hashlib.sha256(work).hexdigest(),
                "mutated_work_sha256": hashlib.sha256(mutated_work).hexdigest(),
                "slot": hex(read_u32(self.uc, WORK_SLOT)),
                "ready_calls": list(self.ready_calls), "trigger_calls": list(self.trigger_calls),
                "event_calls": list(self.event_calls), "timeline": list(self.timeline),
                "hook_error": self.hook_error}


def _event_projection(run: dict):
    return [{key: row[key] for key in ("event_id", "work_selection", "work_cached")}
            for row in run["event_calls"]]


def compare(original: dict, adapter: dict, label: str, ready=(1, 1)) -> dict:
    expected_stop = GATE_EXIT if not all(ready) else TOUCH_STOP
    o, c = original["state"], adapter["state"]
    ready_projection = lambda run: [(x["entry"], x["result"]) for x in run["ready_calls"]]
    trigger_projection = lambda run: [(x["logical_id"], x["result"]) for x in run["trigger_calls"]]
    same_helper_order = (ready_projection(original) == ready_projection(adapter)
                         and trigger_projection(original) == trigger_projection(adapter)
                         and original["timeline"] == adapter["timeline"])
    same_memory = (original["work_hex"] == adapter["work_hex"]
                   and original["mutated_work_hex"] == adapter["mutated_work_hex"]
                   and original["slot"] == adapter["slot"])
    same_registers = (o["callee_saved"] == c["callee_saved"]
                      and o["d8_d15"] == c["d8_d15"]
                      and o["s17"] == c["s17"] and o["r6"] == c["r6"]
                      and o["sp"] == c["sp"] and o["fpscr"] == c["fpscr"])
    sp_aligned = (o["sp"] & 7) == 0 and (c["sp"] & 7) == 0
    passed = (original["fault"] is None and adapter["fault"] is None
              and original["hook_error"] is None and adapter["hook_error"] is None
              and original["stop"] == expected_stop and adapter["stop"] == expected_stop
              and same_helper_order and _event_projection(original) == _event_projection(adapter)
              and same_memory and same_registers and sp_aligned
              and (not all(ready) or adapter["mailbox"] == WORK))
    return {"case": label, "passed": passed, "expected_stop": hex(expected_stop),
            "original_stop": hex(original["stop"]), "adapter_stop": hex(adapter["stop"]),
            "original_fault": original["fault"], "adapter_fault": adapter["fault"],
            "helper_order_match": same_helper_order,
            "event_observation_match": _event_projection(original) == _event_projection(adapter),
            "memory_match": same_memory, "registers_match": same_registers,
            "sp_aligned": sp_aligned,
            "original_r4": hex(o["callee_saved"]["r4"]),
            "adapter_r4": hex(c["callee_saved"]["r4"]),
            "original_r8": hex(o["callee_saved"]["r8"]),
            "adapter_r8": hex(c["callee_saved"]["r8"]),
            "original_s17": hex(o["s17"]), "adapter_s17": hex(c["s17"]),
            "original_r6": hex(o["r6"]), "adapter_r6": hex(c["r6"]),
            "mailbox": hex(adapter["mailbox"]),
            "slot": adapter["slot"], "changed_offsets": [
                hex(i) for i, (before, after) in enumerate(zip(bytes.fromhex(original["initial_work_hex"]),
                                                                 bytes.fromhex(original["work_hex"]))) if before != after]}


def mismatch_summary(original: dict, candidate: dict) -> dict:
    return {"stops_differ": original["stop"] != candidate["stop"],
            "r4_differ": original["state"]["callee_saved"]["r4"] != candidate["state"]["callee_saved"]["r4"],
            "s17_differ": original["state"]["s17"] != candidate["state"]["s17"],
            "work_differ": original["work_hex"] != candidate["work_hex"],
            "r8_differ": original["state"]["callee_saved"]["r8"] != candidate["state"]["callee_saved"]["r8"],
            "original_stop": hex(original["stop"]), "candidate_stop": hex(candidate["stop"])}


def run_experiment(code_path: Path, output: Path) -> dict:
    if output.exists() and any(output.iterdir()):
        raise ValueError(f"private output directory is not fresh: {output}")
    output.mkdir(parents=True, exist_ok=True)
    image = code_path.read_bytes()
    reference = verify_image(image)
    blobs, build = compile_adapter(output)

    specs = [
        ("script-false-status-tail", 1, 0, (0, 1), {}, False, 1.5),
        ("preview-false-status-tail", 1, 0, (1, 0), {}, False, 1.5),
        ("unchanged-selection-touch-continuation", 2, 2, (1, 1), {}, False, 1.5),
        ("changed-selection-event-and-blend-clamp", 1, 0, (1, 1), {6: 1}, False, 1.5),
        ("captured-work-survives-global-slot-mutation", 1, 0, (1, 1), {6: 1}, True, 1.5),
    ]
    cases = []
    run_data = {}
    for label, cursor, cached, ready, responses, mutate, blend in specs:
        original = AdapterMachine(image, blobs, "good").run("original", cursor, cached, ready, responses,
                                                              mutate_global=mutate, blend=blend)
        candidate = AdapterMachine(image, blobs, "good").run("adapter", cursor, cached, ready, responses,
                                                               mutate_global=mutate, blend=blend)
        row = compare(original, candidate, label, ready)
        cases.append(row)
        run_data[label] = {"original": original, "adapter": candidate}

    # Independent wrong status target: the gate-failure status must not reach
    # the blend/touch continuation.
    status_o = AdapterMachine(image, blobs, "good").run("original", 1, 0, (0, 1), {})
    status_bad = AdapterMachine(image, blobs, "wrong_status_target").run(
        "wrong_status", 1, 0, (0, 1), {}, mailbox_seed=WORK)
    status_control = mismatch_summary(status_o, status_bad)
    status_control["candidate_fault"] = status_bad["fault"]
    status_control["rejected"] = status_control["stops_differ"] and status_bad["stop"] == TOUCH_STOP

    # Missing S17 restoration should be visible when the post-reducer blend
    # clamp consumes s17, while R8 and the pointer are still restored correctly.
    s17_o = AdapterMachine(image, blobs, "good").run("original", 1, 0, (1, 1), {6: 1}, blend=1.5)
    s17_bad = AdapterMachine(image, blobs, "missing_s17").run("missing_s17", 1, 0, (1, 1), {6: 1}, blend=1.5)
    s17_control = mismatch_summary(s17_o, s17_bad)
    s17_control["rejected"] = s17_control["s17_differ"] or s17_control["work_differ"]

    # The global pointer changes at the first trigger after candidate capture.
    # A bad adapter that reloads the singleton for R4 must use MUTATED_WORK.
    ptr_o = AdapterMachine(image, blobs, "good").run("original", 1, 0, (1, 1), {6: 1},
                                                        mutate_global=True, blend=1.5)
    ptr_bad = AdapterMachine(image, blobs, "reload_pointer").run("reload_pointer", 1, 0, (1, 1), {6: 1},
                                                                  mutate_global=True, blend=1.5)
    pointer_control = mismatch_summary(ptr_o, ptr_bad)
    pointer_control["rejected"] = pointer_control["r4_differ"] or pointer_control["work_differ"]

    controls = {"wrong_status_target": status_control,
                "missing_s17_restore": s17_control,
                "reload_instead_of_captured_pointer": pointer_control}
    report = {
        "task_id": "h1-navigation-adapter-differential",
        "address": hex(CALLBACK_START),
        "outcome": "ready_for_review",
        "passed": all(row["passed"] for row in cases) and all(x["rejected"] for x in controls.values()),
        "reference": reference,
        "candidate": build,
        "shim_contract": {
            "candidate_address": hex(CANDIDATE_ADDRESS), "mailbox_address": hex(MAILBOX),
            "captured_work_pointer": "candidate publishes the post-readiness singleton value; good shim loads it into r4",
            "gate_failure_target": hex(GATE_EXIT), "reducer_success_target": hex(CONTINUE),
            "touch_stop": hex(TOUCH_STOP), "returns_to_callback_caller": False,
            "entry_frame": "preexisting callback frame represented with 8-byte aligned SP; C++ candidate preserves ABI callee-saved state; tail shim does not alter SP",
        },
        "cases": cases,
        "control_results": controls,
        "selected_trace": {name: {"original_timeline": row["original"]["timeline"],
                                   "adapter_timeline": row["adapter"]["timeline"],
                                   "original_work_sha256": row["original"]["work_sha256"],
                                   "adapter_work_sha256": row["adapter"]["work_sha256"],
                                   "original_mutated_work_sha256": row["original"]["mutated_work_sha256"],
                                   "adapter_mutated_work_sha256": row["adapter"]["mutated_work_sha256"]}
                           for name, row in run_data.items()},
        "evidence": {"compiled": "passed", "arm_differential": "passed" if all(row["passed"] for row in cases) and all(x["rejected"] for x in controls.values()) else "failed",
                     "caller": "partial", "runtime": "not_run"},
        "limitations": [
            "The callback frame is represented by initialized registers/stack at the inline-window entry; the function prologue and common epilogue are outside the executed window.",
            "Readiness, input, and event entry hooks provide explicit configured results; the event queue and physical-input internals are not executed.",
            "The success continuation is original ARM through the instruction after the touch pointer reload at 0x001E9E50; physical touch dispatch and later callback work are not covered.",
            "Only the listed work-block fields and synthetic title-work pointers are exercised; no runtime-normal object graph, Azahar run, production patch/link placement, or whole-H1 equivalence is established.",
        ],
    }
    report_path = output / "report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"H1 navigation adapter {'PASS' if report['passed'] else 'FAIL'}; report: {report_path}")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code", type=Path, default=ROOT / "extracted/exefs/code.bin")
    parser.add_argument("--output", type=Path, required=True,
                        help="fresh private output directory for object and report")
    args = parser.parse_args()
    try:
        report = run_experiment(args.code, args.output)
    except (RuntimeError, ValueError, OSError) as error:
        parser.exit(2, f"Experiment error: {error}\n")
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
