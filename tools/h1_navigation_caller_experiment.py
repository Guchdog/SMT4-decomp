#!/usr/bin/env python3
"""Differentially exercise the isolated H1 navigation caller candidate."""
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
WORK_SLOT = 0x0044E300
WORK = DATA + 0x100
WORK_SIZE = 0xA0
TRIGGER_IDS = (5, 0xE, 6, 0xF)
EXPECTED_SHA256 = "1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558"
INITIAL_CALLEE_SAVED = {f"r{index}": (0xA5000000 + index * 0x10101) & 0xFFFFFFFF
                        for index in range(4, 12)}
INITIAL_CALLEE_SAVED["r4"] = WORK
INITIAL_CALLEE_SAVED["r8"] = 0x88888888
INITIAL_VFP = {f"d{index}": 0x1122334400000000 + index for index in range(8, 16)}
INITIAL_FPSCR = 0x01000000


def verify_image(image: bytes) -> dict:
    digest = hashlib.sha256(image).hexdigest()
    if digest != EXPECTED_SHA256:
        raise ValueError("code.bin SHA-256 does not match the pinned game revision")
    import capstone
    decoder = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    windows = ((CALLBACK_START, CONTINUE), (SCRIPT_READY, SCRIPT_READY + 0x60),
               (PREVIEW_READY, PREVIEW_READY + 0x60),
               (TRIGGER, TRIGGER + 0x80), (EVENT_REQUEST, EVENT_REQUEST + 0x60))
    decoded = []
    for start, stop in windows:
        code = image[start - TEXT:stop - TEXT]
        insns = list(decoder.disasm(code, start))
        if not insns:
            raise ValueError(f"no ARM decode in pinned window {start:#x}..{stop:#x}")
        decoded.append({"start": hex(start), "stop": hex(stop),
                        "first_instructions": [f"{i.address:#x}: {i.mnemonic} {i.op_str}" for i in insns[:5]]})
    return {"sha256": digest, "size": len(image), "windows": decoded}


def read_u32(uc, address: int) -> int:
    return struct.unpack("<I", uc.mem_read(address, 4))[0]


def write_u32(uc, address: int, value: int):
    uc.mem_write(address, struct.pack("<I", value & 0xFFFFFFFF))


def read_u64(uc, address: int) -> int:
    return struct.unpack("<Q", uc.mem_read(address, 8))[0]


def write_u64(uc, address: int, value: int):
    uc.mem_write(address, struct.pack("<Q", value & 0xFFFFFFFFFFFFFFFF))


def memory_digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class CallerMachine:
    def __init__(self, image: bytes, candidate: bytes | None = None,
                 wrong_normalizer: bytes | None = None):
        import unicorn
        from unicorn import arm_const as arm
        self.unicorn, self.arm = unicorn, arm
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.ctl_set_cpu_model(arm.UC_CPU_ARM_11MPCORE)
        self.uc.mem_map(TEXT, 0x400000, unicorn.UC_PROT_READ | unicorn.UC_PROT_WRITE | unicorn.UC_PROT_EXEC)
        self.uc.mem_write(TEXT, image)
        self.uc.mem_map(INJECT, 0x4000, unicorn.UC_PROT_READ | unicorn.UC_PROT_EXEC)
        self.uc.mem_map(DATA, DATA_SIZE, unicorn.UC_PROT_READ | unicorn.UC_PROT_WRITE)
        self.uc.mem_map(STACK, STACK_SIZE, unicorn.UC_PROT_READ | unicorn.UC_PROT_WRITE)
        self.candidate = candidate
        self.wrong_normalizer = wrong_normalizer
        if candidate is not None:
            self.uc.mem_write(INJECT, candidate)
        if wrong_normalizer is not None:
            self.uc.mem_write(INJECT + 0x2000, wrong_normalizer)
        self.ready_results = {SCRIPT_READY: 0, PREVIEW_READY: 0}
        self.trigger_results = {logical_id: 0 for logical_id in TRIGGER_IDS}
        self.ready_calls: list[dict] = []
        self.trigger_calls: list[dict] = []
        self.event_calls: list[dict] = []
        self.stops: tuple[int, ...] = ()
        self.hook_error: str | None = None
        self.uc.hook_add(unicorn.UC_HOOK_CODE, self._hook)

    def _register_snapshot(self):
        a = self.arm
        return {"r0": self.uc.reg_read(a.UC_ARM_REG_R0),
                "r1": self.uc.reg_read(a.UC_ARM_REG_R1),
                "r2": self.uc.reg_read(a.UC_ARM_REG_R2),
                "r3": self.uc.reg_read(a.UC_ARM_REG_R3),
                "sp": self.uc.reg_read(a.UC_ARM_REG_SP),
                "lr": self.uc.reg_read(a.UC_ARM_REG_LR)}

    def _hook(self, uc, address, _size, _user):
        if address in self.stops:
            uc.emu_stop()
            return
        a = self.arm
        if address in (SCRIPT_READY, PREVIEW_READY):
            call = self._register_snapshot()
            call["entry"] = hex(address)
            call["result"] = int(self.ready_results[address])
            self.ready_calls.append(call)
            uc.reg_write(a.UC_ARM_REG_R0, int(self.ready_results[address]))
            uc.reg_write(a.UC_ARM_REG_PC, uc.reg_read(a.UC_ARM_REG_LR))
        elif address == TRIGGER:
            call = self._register_snapshot()
            logical_id = call["r0"]
            call["entry"] = hex(address)
            if logical_id not in self.trigger_results:
                self.hook_error = f"unexpected trigger ID {logical_id:#x}"
                uc.emu_stop()
                return
            call["logical_id"] = logical_id
            call["result"] = int(self.trigger_results[logical_id])
            self.trigger_calls.append(call)
            uc.reg_write(a.UC_ARM_REG_R0, int(self.trigger_results[logical_id]))
            uc.reg_write(a.UC_ARM_REG_PC, uc.reg_read(a.UC_ARM_REG_LR))
        elif address == EVENT_REQUEST:
            call = self._register_snapshot()
            call.update({"entry": hex(address), "event_id": call["r0"],
                         "work_selection": read_u32(uc, WORK + 8),
                         "work_cached": read_u32(uc, WORK + 12)})
            self.event_calls.append(call)
            # Harness boundary hook only: record the external call then return.
            uc.reg_write(a.UC_ARM_REG_PC, uc.reg_read(a.UC_ARM_REG_LR))

    def initialize(self, cursor: int, cached: int, script_ready: int, preview_ready: int):
        a = self.arm
        self.uc.mem_write(DATA, bytes(DATA_SIZE))
        self.uc.mem_write(STACK, bytes(STACK_SIZE))
        pattern = bytes(((index * 37 + 0x5B) & 0xFF) for index in range(WORK_SIZE))
        self.uc.mem_write(WORK, pattern)
        write_u32(self.uc, WORK_SLOT, WORK)
        write_u32(self.uc, WORK + 8, cursor)
        write_u32(self.uc, WORK + 12, cached)
        # finite, exactly representable float to make +1 deterministic
        self.uc.mem_write(WORK + 0x64, struct.pack("<f", 12.5))
        self.uc.reg_write(a.UC_ARM_REG_CPSR, 0x10)
        self.uc.reg_write(a.UC_ARM_REG_SP, STACK + 0x1800)
        self.uc.reg_write(a.UC_ARM_REG_LR, RETURN)
        self.uc.reg_write(a.UC_ARM_REG_R0, 0x51515151)
        self.uc.reg_write(a.UC_ARM_REG_R1, 0x61616161)
        self.uc.reg_write(a.UC_ARM_REG_R2, 0x72727272)
        self.uc.reg_write(a.UC_ARM_REG_R3, 0x83838383)
        for name, value in INITIAL_CALLEE_SAVED.items():
            uc_id = getattr(a, f"UC_ARM_REG_{name.upper()}")
            self.uc.reg_write(uc_id, value)
        for name, value in INITIAL_VFP.items():
            self.uc.reg_write(getattr(a, f"UC_ARM_REG_{name.upper()}"), value)
        self.uc.reg_write(a.UC_ARM_REG_FPSCR, INITIAL_FPSCR)
        # ARM11 model requires explicit VFP access and enable state.
        self.uc.reg_write(a.UC_ARM_REG_C1_C0_2, 0x00F00000)
        self.uc.reg_write(a.UC_ARM_REG_FPEXC, 0x40000000)
        self.ready_results = {SCRIPT_READY: int(script_ready), PREVIEW_READY: int(preview_ready)}
        self.ready_calls.clear()
        self.trigger_calls.clear()
        self.event_calls.clear()
        self.hook_error = None
        return pattern

    def state(self):
        a = self.arm
        return {
            "pc": self.uc.reg_read(a.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(a.UC_ARM_REG_SP),
            "lr": self.uc.reg_read(a.UC_ARM_REG_LR),
            "callee_saved": {name: self.uc.reg_read(getattr(a, f"UC_ARM_REG_{name.upper()}"))
                             for name in INITIAL_CALLEE_SAVED},
            "vfp_d8_d15": {name: self.uc.reg_read(getattr(a, f"UC_ARM_REG_{name.upper()}"))
                           for name in INITIAL_VFP},
            "fpscr": self.uc.reg_read(a.UC_ARM_REG_FPSCR),
        }

    def run_original(self, cursor: int, cached: int, ready=(1, 1), responses=None):
        self.initialize(cursor, cached, ready[0], ready[1])
        self.trigger_results = {key: int((responses or {}).get(key, 0)) for key in TRIGGER_IDS}
        self.stops = (CONTINUE, GATE_EXIT)
        initial = bytes(self.uc.mem_read(WORK, WORK_SIZE))
        try:
            self.uc.emu_start(CALLBACK_START, 0, count=512)
            fault = None
        except self.unicorn.UcError as error:
            fault = str(error)
        final = bytes(self.uc.mem_read(WORK, WORK_SIZE))
        return {"fault": fault, "stop": self.uc.reg_read(self.arm.UC_ARM_REG_PC),
                "state": self.state(), "work_hex": final.hex(), "initial_work_hex": initial.hex(),
                "work_sha256": memory_digest(final), "initial_work_sha256": memory_digest(initial),
                "ready_calls": list(self.ready_calls), "trigger_calls": list(self.trigger_calls),
                "event_calls": list(self.event_calls), "hook_error": self.hook_error}

    def run_candidate(self, cursor: int, cached: int, ready=(1, 1), responses=None):
        if self.candidate is None:
            raise ValueError("candidate blob is not loaded")
        initial = self.initialize(cursor, cached, ready[0], ready[1])
        self.trigger_results = {key: int((responses or {}).get(key, 0)) for key in TRIGGER_IDS}
        self.stops = (RETURN,)
        try:
            self.uc.emu_start(INJECT, 0, count=1024)
            fault = None
        except self.unicorn.UcError as error:
            fault = str(error)
        final = bytes(self.uc.mem_read(WORK, WORK_SIZE))
        return {"fault": fault, "stop": self.uc.reg_read(self.arm.UC_ARM_REG_PC),
                "state": self.state(), "return": self.uc.reg_read(self.arm.UC_ARM_REG_R0),
                "work_hex": final.hex(), "initial_work_hex": initial.hex(), "work_sha256": memory_digest(final),
                "initial_work_sha256": memory_digest(initial),
                "ready_calls": list(self.ready_calls), "trigger_calls": list(self.trigger_calls),
                "event_calls": list(self.event_calls), "hook_error": self.hook_error}

    def run_wrong_normalizer(self, value: int):
        if self.wrong_normalizer is None:
            raise ValueError("wrong-normalizer control is not loaded")
        self.initialize(value, 0, 1, 1)
        self.uc.reg_write(self.arm.UC_ARM_REG_R0, value & 0xFFFFFFFF)
        self.stops = (RETURN,)
        self.uc.emu_start(INJECT + 0x2000, 0, count=128)
        return self.uc.reg_read(self.arm.UC_ARM_REG_R0)


def compile_candidate(output: Path) -> tuple[bytes, bytes, dict]:
    source = ROOT / "experiments/semantic_equivalence/h1_navigation_caller_candidate.cpp"
    obj = output / "h1_navigation_caller_candidate.o"
    build = compile_tu_armv6k(source, obj, ROOT)
    if build.returncode:
        raise RuntimeError(build.stderr or "ARMv6K candidate compilation failed")
    funcs = extract_elf_functions_detailed(obj)
    required = ("h1_navigation_caller_candidate", "h1_navigation_wrong_raw_signed_modulo")
    validation = []
    for name in required:
        if name not in funcs:
            raise ValueError(f"missing candidate symbol {name}")
        code, relocations = funcs[name]
        if relocations:
            raise ValueError(f"unsupported relocations in {name}: {relocations}")
        validation.append(validate_candidate_blob(code, name))
    candidate, _ = funcs[required[0]]
    wrong, _ = funcs[required[1]]
    metadata = {"source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                "object_sha256": hashlib.sha256(obj.read_bytes()).hexdigest(),
                "candidate_sha256": hashlib.sha256(candidate).hexdigest(),
                "candidate_size": len(candidate), "wrong_control_sha256": hashlib.sha256(wrong).hexdigest(),
                "compiler_stdout": build.stdout, "compiler_stderr": build.stderr,
                "symbol_validation": validation}
    return candidate, wrong, metadata


def validate_candidate_blob(code: bytes, name: str):
    import capstone
    import capstone.arm as arm
    decoder = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    decoder.detail = True
    insns = list(decoder.disasm(code, INJECT))
    if not insns:
        raise ValueError(f"no decoded ARM instructions in {name}")
    # Prove a trailing pool from both the branch-over boundary and every
    # PC-relative data reference; arbitrary undecoded symbol tails are rejected.
    unconditional = [i for i in insns if i.mnemonic == "b" and i.operands
                     and i.operands[0].type == arm.ARM_OP_IMM]
    pc_refs = set()
    for insn in insns:
        for operand in insn.operands:
            if operand.type == arm.ARM_OP_MEM and operand.mem.base == arm.ARM_REG_PC:
                pc_refs.add((insn.address + 8 + operand.mem.disp) & 0xFFFFFFFF)
    pool_start = None
    for branch in reversed(unconditional):
        boundary = branch.address + branch.size
        refs = sorted(address for address in pc_refs if address >= boundary)
        if not refs:
            continue
        candidate_start, pool_end = refs[0], refs[-1] + 4
        if (candidate_start == boundary and pool_end == INJECT + len(code)
                and pool_end - candidate_start <= 16
                and (pool_end - candidate_start) % 4 == 0
                and refs == list(range(candidate_start, pool_end, 4))):
            targets_pool = any(
                operand.type == arm.ARM_OP_IMM and candidate_start <= operand.imm < pool_end
                for insn in insns for operand in insn.operands
                if insn.mnemonic in ("b", "bl", "blx", "cbz", "cbnz"))
            if not targets_pool:
                pool_start = candidate_start
                break
    if pool_start is None and sum(i.size for i in insns) != len(code):
        raise ValueError(f"undecoded ARM bytes or unproven literal pool in {name}")
    if pool_start is not None:
        body = [insn for insn in insns if insn.address < pool_start]
        if (not body or body[0].address != INJECT
                or body[-1].address + body[-1].size != pool_start
                or any(left.address + left.size != right.address
                       for left, right in zip(body, body[1:]))):
            raise ValueError(f"instruction boundaries do not exactly reach literal pool in {name}")
        branch = next((insn for insn in reversed(unconditional)
                       if insn.address + insn.size == pool_start), None)
        if (branch is None or branch.operands[0].imm >= pool_start
                or branch.operands[0].imm < INJECT):
            raise ValueError(f"no in-blob unconditional branch skips literal pool in {name}")
    # Calls through the explicit pinned helper pointers compile to BLX register.
    # Reject direct calls and any PC-relative transfer leaving the blob.
    for insn in insns:
        if insn.mnemonic == "bl":
            raise ValueError(f"unexpected direct BL in {name}: {insn.op_str}")
        if insn.mnemonic == "blx" and insn.op_str.startswith("#"):
            raise ValueError(f"unexpected immediate BLX in {name}: {insn.op_str}")
    return {"symbol": name, "bytes": len(code),
            "literal_pool": None if pool_start is None else {
                "start": hex(pool_start), "size": INJECT + len(code) - pool_start,
                "referenced_words": [hex(address) for address in sorted(pc_refs) if address >= pool_start],
                "branch_over_pool": f"{branch.address:#x} -> {branch.operands[0].imm:#x}"},
            "decoded_instruction_bytes": len(code) if pool_start is None else pool_start - INJECT}


def compare_case(image: bytes, candidate: bytes, wrong: bytes, label: str,
                 cursor: int, cached: int, ready=(1, 1), responses=None) -> dict:
    original = CallerMachine(image).run_original(cursor, cached, ready, responses)
    rebuilt = CallerMachine(image, candidate, wrong).run_candidate(cursor, cached, ready, responses)
    continuation = CONTINUE if all(ready) else GATE_EXIT
    original_trigger_calls = [item["logical_id"] for item in original["trigger_calls"]]
    candidate_trigger_calls = [item["logical_id"] for item in rebuilt["trigger_calls"]]
    original_event = [{key: item[key] for key in ("event_id", "work_selection", "work_cached")}
                      for item in original["event_calls"]]
    candidate_event = [{key: item[key] for key in ("event_id", "work_selection", "work_cached")}
                       for item in rebuilt["event_calls"]]
    work_match = original["work_hex"] == rebuilt["work_hex"]
    work_original = bytes.fromhex(original["work_hex"])
    work_candidate = bytes.fromhex(rebuilt["work_hex"])
    work_initial = bytes.fromhex(original["initial_work_hex"])
    touched = [index for index, (before, after) in enumerate(zip(work_initial, work_original))
               if before != after]
    permitted_touched = set(range(0x08, 0x10)) | set(range(0x64, 0x68))
    untouched_match = all(work_original[index] == work_candidate[index]
                          for index in range(WORK_SIZE) if index not in permitted_touched)
    helper_match = (original["ready_calls"] and
                    [item["entry"] for item in original["ready_calls"]] ==
                    [item["entry"] for item in rebuilt["ready_calls"]] and
                    original_trigger_calls == candidate_trigger_calls)
    state_original, state_candidate = original["state"], rebuilt["state"]
    callee_delta = {name: {"original": state_original["callee_saved"][name],
                           "candidate": state_candidate["callee_saved"][name]}
                    for name in state_original["callee_saved"]
                    if state_original["callee_saved"][name] != state_candidate["callee_saved"][name]}
    vfp_delta = {name: {"original": state_original["vfp_d8_d15"][name],
                        "candidate": state_candidate["vfp_d8_d15"][name]}
                 for name in state_original["vfp_d8_d15"]
                 if state_original["vfp_d8_d15"][name] != state_candidate["vfp_d8_d15"][name]}
    behavior_match = (original["fault"] is None and rebuilt["fault"] is None
                      and original["stop"] == continuation and rebuilt["stop"] == RETURN
                      and not original["hook_error"] and not rebuilt["hook_error"]
                      and work_match and untouched_match and helper_match and original_event == candidate_event
                      and state_original["sp"] == state_candidate["sp"]
                      and state_original["fpscr"] == state_candidate["fpscr"])
    full_state_match = behavior_match and not callee_delta and not vfp_delta
    return {"case": label, "input": {"cursor": cursor, "cached": cached,
                                       "ready": list(ready), "responses": responses or {}},
            "passed_behavior": behavior_match, "passed_full_state": full_state_match,
            "memory_match": work_match, "untouched_bytes_match": untouched_match,
            "changed_work_offsets": [hex(index) for index in touched],
            "helper_order_match": helper_match, "event_call_match": original_event == candidate_event,
            "continuation_original": hex(original["stop"]), "continuation_candidate_return": hex(rebuilt["stop"]),
            "callee_saved_deltas": callee_delta, "vfp_deltas": vfp_delta,
            "original": original, "candidate": rebuilt}


def run(code_path: Path, output: Path) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    image = code_path.read_bytes()
    reference = verify_image(image)
    candidate, wrong, compiled = compile_candidate(output)
    readiness_cases = [
        compare_case(image, candidate, wrong, "script-not-ready-skips-preview-and-input", 1, 0,
                     (0, 0), {}),
        compare_case(image, candidate, wrong, "preview-not-ready-skips-input", 1, 0,
                     (1, 0), {}),
        compare_case(image, candidate, wrong, "both-ready-no-input", 1, 0, (1, 1), {}),
    ]
    directed = [
        ("previous-primary-wrap", 0, 0, {5: 1}),
        ("previous-alias-wrap", 0, 0, {0xE: 1}),
        ("previous-primary-wins-alias", 2, 1, {5: 1, 0xE: 1}),
        ("next-primary-wrap", 3, 3, {6: 1}),
        ("next-alias-wrap", 3, 3, {0xF: 1}),
        ("next-primary-wins-alias", 2, 2, {6: 1, 0xF: 1}),
        ("both-directions-net-zero", 0, 0, {5: 1, 6: 1}),
        ("both-aliases-net-zero", 1, 1, {0xE: 1, 0xF: 1}),
        ("change-event-before-cache-write", 1, 0, {6: 1}),
        ("unchanged-no-event", 1, 1, {}),
    ]
    directed_results = [compare_case(image, candidate, wrong, name, cur, cache, (1, 1), responses)
                        for name, cur, cache, responses in directed]
    exhaustive = []
    for cursor in range(4):
        for cached in range(4):
            for bits in range(16):
                responses = {logical_id: int(bool(bits & (1 << index)))
                             for index, logical_id in enumerate(TRIGGER_IDS)}
                exhaustive.append(compare_case(image, candidate, wrong,
                                               f"valid-c{cursor}-cache{cached}-mask{bits:02x}",
                                               cursor, cached, (1, 1), responses))
    negative = CallerMachine(image, candidate, wrong)
    wrong_minus_one = negative.run_wrong_normalizer(0xFFFFFFFF)
    negative_control = {"input": "signed provisional -1", "original_result": 3,
                        "wrong_raw_signed_modulo_result": wrong_minus_one,
                        "rejected": wrong_minus_one != 3}
    report = {
        "passed": (all(case["passed_behavior"] for case in readiness_cases + directed_results + exhaustive)
                   and negative_control["rejected"]),
        "scope": "compiled H1 readiness + state-5 keyboard/controller reducer caller window, ending before blend/touch",
        "reference": reference,
        "candidate": compiled,
        "hook_contract": {
            "allowed_entry_hooks_only": [hex(SCRIPT_READY), hex(PREVIEW_READY), hex(TRIGGER), hex(EVENT_REQUEST)],
            "readiness": "no formal arguments; r0 return; hook returns configured test value",
            "trigger": "one u32 logical ID in r0; s32 result in r0; hooks record entry registers and return configured test value",
            "event": "one u32 event ID in r0; void-like return; hook records r0-r3, SP and work+8/+0xc then returns",
            "internal_candidate_behavior": "not hooked or synthesized",
        },
        "readiness_cases": readiness_cases,
        "directed_cases": directed_results,
        "exhaustive_valid_domain": {"case_count": len(exhaustive),
                                    "passed": all(x["passed_behavior"] for x in exhaustive),
                                    "full_state_match": all(x["passed_full_state"] for x in exhaustive),
                                    "cursor": [0, 1, 2, 3], "cache": [0, 1, 2, 3], "trigger_masks": 16,
                                    "cases": [{"case": x["case"], "input": x["input"],
                                               "passed_behavior": x["passed_behavior"],
                                               "trigger_order_original": [z["logical_id"] for z in x["original"]["trigger_calls"]],
                                               "trigger_order_candidate": [z["logical_id"] for z in x["candidate"]["trigger_calls"]],
                                               "events_original": [{"id": z["event_id"], "selection": z["work_selection"], "cached": z["work_cached"]}
                                                                   for z in x["original"]["event_calls"]],
                                               "events_candidate": [{"id": z["event_id"], "selection": z["work_selection"], "cached": z["work_cached"]}
                                                                     for z in x["candidate"]["event_calls"]],
                                               "selection_original": int.from_bytes(bytes.fromhex(x["original"]["work_hex"])[8:12], "little"),
                                               "selection_candidate": int.from_bytes(bytes.fromhex(x["candidate"]["work_hex"])[8:12], "little"),
                                               "cached_original": int.from_bytes(bytes.fromhex(x["original"]["work_hex"])[12:16], "little"),
                                               "cached_candidate": int.from_bytes(bytes.fromhex(x["candidate"]["work_hex"])[12:16], "little")}
                                              for x in exhaustive]},
        "negative_control": negative_control,
        "evidence": {"compiled": "passed", "arm_differential": "partial" if not all(x["passed_full_state"] for x in readiness_cases + directed_results + exhaustive) else "passed",
                     "caller": "partial", "runtime": "not_run"},
        "limitations": [
            "Harness hooks replace only external helper entry PCs; readiness/input outcomes and event queue internals are still explicit test boundaries.",
            "Raw caller continuation has callee-saved register and VFP differences because the original inline window has side effects (R4/R8 and S17/D8), while standalone C++ obeys the AAPCS callee-preservation contract; report these rather than claiming raw-PC substitutability.",
            "The candidate reaches its return sentinel, not original PC 0x001E9DE0; it does not execute the subsequent blend, touch, help-text, fade, or dispatch path.",
            "Physical controls, held-input filtering, real event queue state, visual presentation, and whole-game behavior are not established.",
            "The valid exhaustive cursor/cache domain is 0..3. The -1 negative control validates only rejection of raw signed remainder, not arbitrary corrupted work-state behavior.",
        ],
    }
    path = output / "report.json"
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"H1 navigation caller experiment {'BEHAVIOR PASS; STATE PARTIAL' if report['passed'] else 'FAIL'}; report: {path}")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code", type=Path, default=ROOT / "extracted/exefs/code.bin")
    parser.add_argument("--output", type=Path, required=True,
                        help="fresh private output directory for object and report")
    args = parser.parse_args()
    try:
        report = run(args.code, args.output)
    except (RuntimeError, ValueError, OSError) as error:
        parser.exit(2, f"Experiment error: {error}\n")
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
