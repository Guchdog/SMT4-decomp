#!/usr/bin/env python3
"""Compose the pinned title State-9/10 caller with original/candidate H2 init."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import unicorn
from unicorn import arm_const as arm
from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k, find_clang

CODE_DEFAULT = ROOT / "extracted/exefs/code.bin"
EXPECTED_CODE_SHA256 = "1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558"
EXPECTED_CALC_PATCH_SHA256 = "c9ebf62679043512c22c684b50f9e9cbf1fe824e016f119c2de4bddf664eb45d"
TEXT = 0x00100000
TEXT_MAP_SIZE = 0x00480000
INJECT = 0x01000000
INJECT_MAP_SIZE = 0x6000
INIT_INJECT = INJECT + 0x4000
RETURN = INJECT + INJECT_MAP_SIZE - 4
DATA = 0x02000000
DATA_SIZE = 0x10000
TITLE_MAIN_WORK = DATA + 0x100
TITLE_CONFIG_WORK = DATA + 0x2000
SPRITE_TABLE = DATA + 0x800
STACK = 0x08000000
STACK_SIZE = 0x8000
INITIAL_SP = STACK + STACK_SIZE // 2
CALLBACK = 0x001E989C
INIT = 0x002F4CA0
READY = 0x002FC0EC
TASK_ACTIVE = 0x002BF41C
TITLE_MAIN_GLOBAL = 0x0044E300
TITLE_CONFIG_GLOBAL = 0x0044E2D0
CONFIG = 0x0044E0F8
INIT_SOURCE = ROOT / "experiments/semantic_equivalence/h2_init_orchestration_candidate.cpp"
INIT_SYMBOL = "candidate_002f4ca0"
CALC_CALLBACK = 0x001EA928
SECONDARY_CALLBACK = 0x002CAEF0
DRAW_CALLBACK = 0x002CAFD0
CALC_TASK_TOKEN = 0x01110001
DRAW_TASK_TOKEN = 0x01110002

# Called boundaries recorded during init, title handoff, readiness, and reset.
OBSERVED = {
    INIT: "title_config_init_entry",
    0x002A7604: "script_prepare_transition_hle",
    0x002C4B84: "allocator_hle",
    0x002C5978: "create_calc_wrapper",
    0x002C4C00: "create_draw_wrapper",
    0x00118488: "process_factory_hle",
    0x002C3344: "sprite_group_init_original",
    0x002C32F8: "sprite_group_bind_original",
    0x002BDB2C: "sprite_setup_hle",
    0x002BDAC0: "sprite_set_anim_original",
    0x0029FAE8: "cursor_setup_hle",
    0x0027EDF8: "fill_pair_original",
    0x00297704: "load_table_hle",
    0x002B8B78: "opaque_2b8b78_hle",
    0x0029F10C: "opaque_reset_mode_hle",
    0x002CAB70: "mapper_a_original",
    0x0021F39C: "mapper_b_original",
    0x002E0AF4: "mapper_c_original",
    0x002ADB40: "copy_pair_original",
    READY: "title_config_ready_original",
    TASK_ACTIVE: "task_active_hle",
    0x002B88C4: "touch_register_hle",
    0x00275E58: "cursor_mode_hle",
    0x002A0C54: "bcenv_load_hle",
    0x002A06DC: "model_visibility_hle",
}
HLE = {
    0x002A7604, 0x002C4B84, 0x00118488, 0x002BDB2C, 0x0029FAE8,
    0x00297704, 0x002B8B78, 0x0029F10C, TASK_ACTIVE, 0x002B88C4,
    0x00275E58, 0x002A0C54, 0x002A06DC,
}

SAVED_GPRS = tuple(getattr(arm, f"UC_ARM_REG_R{i}") for i in range(4, 12))
SAVED_VFPS = tuple(getattr(arm, f"UC_ARM_REG_D{i}") for i in range(8, 16))


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def arm_branch(source: int, target: int) -> bytes:
    displacement = target - (source + 8)
    if displacement & 3 or not -(1 << 25) <= displacement < (1 << 25):
        raise ValueError(f"ARM branch out of range: {source:#x} -> {target:#x}")
    return struct.pack("<I", 0xEA000000 | ((displacement >> 2) & 0xFFFFFF))


def compile_candidate(output: Path) -> tuple[bytes, dict]:
    obj = output / "h2_init_orchestration_candidate.o"
    build = compile_tu_armv6k(INIT_SOURCE, obj, ROOT)
    if build.returncode:
        raise RuntimeError(build.stderr or "ARMv6K initializer candidate compilation failed")
    symbols = extract_elf_functions_detailed(obj)
    if INIT_SYMBOL not in symbols:
        raise ValueError(f"candidate object missing {INIT_SYMBOL}")
    body, relocations = symbols[INIT_SYMBOL]
    if relocations:
        raise ValueError(f"unexpected candidate relocations: {relocations}")
    meta = {"object_sha256": sha256_file(obj), "object_path": str(obj),
            "candidate_bytes": len(body), "compile_exit": build.returncode,
            "compile_command": list(build.args),
            "compiler": subprocess.run([str(find_clang()), "--version"],
                                        check=True, capture_output=True, text=True)
            .stdout.splitlines()[0], "relocations": []}
    return body, meta


def decode_cstr(uc, address: int, limit: int = 128) -> str:
    if not address:
        return "<null>"
    try:
        data = bytearray()
        for offset in range(limit):
            byte = bytes(uc.mem_read(address + offset, 1))[0]
            if byte == 0:
                break
            data.append(byte)
        return data.decode("ascii", "replace")
    except unicorn.UcError:
        return f"<unmapped:{address:#x}>"


def stack_words(uc, sp: int, count: int = 7) -> list[int]:
    try:
        return list(struct.unpack("<" + "I" * count, uc.mem_read(sp, 4 * count)))
    except unicorn.UcError:
        return []


def make_candidate_negative_control(body: bytes) -> tuple[bytes, dict]:
    old = struct.pack("<I", CALC_CALLBACK)
    new = struct.pack("<I", CALC_CALLBACK + 4)
    offsets = [index for index in range(len(body)) if body.startswith(old, index)]
    if len(offsets) != 1:
        raise ValueError(f"expected one Calc callback literal in candidate, found {offsets}")
    mutant = bytearray(body)
    mutant[offsets[0]:offsets[0] + 4] = new
    return bytes(mutant), {"name": "wrong-primary-calc-callback-address",
                           "literal_offset": hex(offsets[0]),
                           "expected": hex(CALC_CALLBACK), "mutated": hex(CALC_CALLBACK + 4)}


def scenario_specs() -> list[dict]:
    return [
        {"label": "baseline-state9-pending-ready", "config": bytes.fromhex("3250503000000000"),
         "flag_7c": 0, "active_sequence": [1, 0], "kind": "transition"},
        {"label": "distinct-config-state9-pending-ready", "config": bytes.fromhex("0113273B4D5F7183"),
         "flag_7c": 0, "active_sequence": [1, 0], "kind": "transition"},
        {"label": "state9-flag-gate", "config": bytes.fromhex("3250503000000000"),
         "flag_7c": 1, "active_sequence": [], "kind": "gate"},
    ]


class CallerMachine:
    def __init__(self, image: bytes, candidate: bytes | None, scenario: dict):
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.ctl_set_cpu_model(arm.UC_CPU_ARM_11MPCORE)
        self.uc.mem_map(TEXT, TEXT_MAP_SIZE,
                        unicorn.UC_PROT_READ | unicorn.UC_PROT_WRITE | unicorn.UC_PROT_EXEC)
        self.uc.mem_write(TEXT, image)
        self.uc.mem_map(INJECT, INJECT_MAP_SIZE,
                        unicorn.UC_PROT_READ | unicorn.UC_PROT_WRITE | unicorn.UC_PROT_EXEC)
        self.uc.mem_map(DATA, DATA_SIZE, unicorn.UC_PROT_READ | unicorn.UC_PROT_WRITE)
        self.uc.mem_map(STACK, STACK_SIZE, unicorn.UC_PROT_READ | unicorn.UC_PROT_WRITE)
        if candidate is not None:
            self.uc.mem_write(INIT_INJECT, candidate)
            self.uc.mem_write(INIT, arm_branch(INIT, INIT_INJECT))
        self.scenario = scenario
        self.trace: list[dict] = []
        self.task_records: list[dict] = []
        self.active_results = list(scenario["active_sequence"])
        self.active_index = 0
        self.touch_index = 0
        self.next_task_token = CALC_TASK_TOKEN
        self.fault: str | None = None
        self.stopped = False
        self.hook_error: str | None = None
        self.tick_results: list[dict] = []
        self._initialize()
        self.uc.hook_add(unicorn.UC_HOOK_CODE, self._on_code)

    def _initialize(self):
        uc = self.uc
        uc.mem_write(DATA, bytes([0xCC]) * DATA_SIZE)
        uc.mem_write(STACK, bytes([0xCD]) * STACK_SIZE)
        title = bytearray(((index * 37 + 0x5B) & 0xFF) for index in range(0xA0))
        struct.pack_into("<I", title, 0x7C, self.scenario["flag_7c"])
        struct.pack_into("<I", title, 0x88, 0xCAFE0088)
        struct.pack_into("<I", title, 0x9C, 9)
        # Start with values which make reset stores observable.
        struct.pack_into("<ff", title, 0x64, 12.5, -3.25)
        struct.pack_into("<HHHH", title, 0x74, 0xAAAA, 0xBBBB, 0xCCCC, 0xDDDD)
        for offset in (0x61, 0x84, 0x85, 0x96):
            title[offset] = 0xA5
        uc.mem_write(TITLE_MAIN_WORK, bytes(title))
        config_work = bytes([0xD7]) * 0x158
        uc.mem_write(TITLE_CONFIG_WORK, config_work)
        uc.mem_write(SPRITE_TABLE, struct.pack("<4h", 12, 24, 36, 48))
        uc.mem_write(TITLE_MAIN_GLOBAL, struct.pack("<I", TITLE_MAIN_WORK))
        uc.mem_write(TITLE_CONFIG_GLOBAL, struct.pack("<I", 0xDEAD0001))
        uc.mem_write(CONFIG, self.scenario["config"])

    def _seed_registers(self):
        uc = self.uc
        uc.reg_write(arm.UC_ARM_REG_CPSR, 0x10)
        uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)
        uc.reg_write(arm.UC_ARM_REG_C1_C0_2, 0x00F00000)
        for index in range(13):
            uc.reg_write(getattr(arm, f"UC_ARM_REG_R{index}"), (0x51510000 + index * 0x10101) & 0xFFFFFFFF)
        uc.reg_write(arm.UC_ARM_REG_R0, 0xCAFEBABE)
        for index, reg in enumerate(SAVED_GPRS):
            uc.reg_write(reg, 0xA5A50000 + index * 0x10101)
        uc.reg_write(arm.UC_ARM_REG_SP, INITIAL_SP)
        uc.reg_write(arm.UC_ARM_REG_LR, RETURN)
        for index, reg in enumerate(SAVED_VFPS):
            uc.reg_write(reg, 0x1122334455667700 + index)
        uc.reg_write(arm.UC_ARM_REG_FPSCR, 0x01000000)

    def _capture(self, address: int) -> dict:
        uc = self.uc
        r = [uc.reg_read(getattr(arm, f"UC_ARM_REG_R{i}")) for i in range(4)]
        sp = uc.reg_read(arm.UC_ARM_REG_SP)
        record = {"address": f"0x{address:08x}", "name": OBSERVED[address],
                  "call_site": f"0x{(uc.reg_read(arm.UC_ARM_REG_LR) - 4) & 0xFFFFFFFF:08x}",
                  "r0_r3": [f"0x{x:08x}" for x in r],
                  "stack_words": [f"0x{x:08x}" for x in stack_words(uc, sp)],
                  "s0_s3_bits": [f"0x{uc.reg_read(getattr(arm, f'UC_ARM_REG_S{i}')):08x}" for i in range(4)]}
        if address in (0x00118488, 0x002C5978, 0x002C4C00,
                       0x00297704, 0x002A0C54):
            record["r0_string"] = decode_cstr(uc, r[0])
        self.trace.append(record)
        return record

    def _hle_return(self, value: int):
        uc = self.uc
        uc.reg_write(arm.UC_ARM_REG_R0, value & 0xFFFFFFFF)
        uc.reg_write(arm.UC_ARM_REG_PC, uc.reg_read(arm.UC_ARM_REG_LR))

    def _on_code(self, uc, address: int, _size: int, _):
        if address == RETURN:
            self.stopped = True
            uc.emu_stop()
            return
        if address not in OBSERVED:
            return
        record = self._capture(address)
        if address not in HLE:
            return
        if address == 0x002A7604:
            self._hle_return(0)
        elif address == 0x002C4B84:
            uc.mem_write(TITLE_CONFIG_WORK, bytes(((i * 37 + 0xA7) & 0xFF) for i in range(0x158)))
            self._hle_return(TITLE_CONFIG_WORK)
        elif address == 0x00118488:
            name = record.get("r0_string")
            if name == "TITLE_CONFIG_MAIN":
                token = CALC_TASK_TOKEN
            elif name == "TITLE_CONFIG D":
                token = DRAW_TASK_TOKEN
            else:
                self.hook_error = f"unexpected process-factory task name: {name!r}"
                uc.emu_stop()
                return
            record["hle_return"] = f"0x{token:08x}"
            self.task_records.append(record)
            self._hle_return(token)
        elif address == 0x002BDB2C:
            sprite = record["r0_r3"][0]
            sprite_ptr = int(sprite, 16)
            uc.mem_write(sprite_ptr + 0x4C, struct.pack("<I", SPRITE_TABLE))
            self._hle_return(0xC001C0DE)
        elif address == 0x0029FAE8:
            self._hle_return(0xC001C0DE)
        elif address == 0x00297704:
            self._hle_return(0xABCD0001)
        elif address == 0x002B8B78:
            # The pinned TitleConfig caller and the callee prototype identify
            # this as Sound_PlaySE(s32 se_id): only r0 is consumed. Keep r1-r3
            # in raw trace evidence, but do not interpret caller-saved scratch.
            if record["r0_r3"][0] not in ("0x00000099", "0x0000009f"):
                self.hook_error = f"unexpected Sound_PlaySE se_id {record['r0_r3'][0]}"
            self._hle_return(0)
        elif address == 0x0029F10C:
            self._hle_return(0xABCD0003)
        elif address == TASK_ACTIVE:
            handle = uc.reg_read(arm.UC_ARM_REG_R0)
            record["task_handle"] = f"0x{handle:08x}"
            if handle != CALC_TASK_TOKEN:
                self.hook_error = f"readiness queried unexpected task handle {handle:#x}"
                self._hle_return(0)
                return
            if self.active_index >= len(self.active_results):
                self.hook_error = "task-active HLE schedule exhausted"
                self._hle_return(0)
                return
            active = self.active_results[self.active_index]
            self.active_index += 1
            record["active_result"] = active
            self._hle_return(active)
        elif address == 0x002B88C4:
            handle = 0x210 + self.touch_index
            self.touch_index += 1
            record["hle_return"] = handle
            self._hle_return(handle)
        elif address in (0x00275E58, 0x002A0C54, 0x002A06DC):
            self._hle_return(0)

    def _snapshot(self) -> dict:
        uc = self.uc
        title = bytes(uc.mem_read(TITLE_MAIN_WORK, 0xA0))
        config_work_ptr = struct.unpack("<I", uc.mem_read(TITLE_CONFIG_GLOBAL, 4))[0]
        config_work = bytes(uc.mem_read(TITLE_CONFIG_WORK, 0x158))
        saved = [uc.reg_read(reg) for reg in SAVED_GPRS]
        saved += [uc.reg_read(reg) for reg in SAVED_VFPS]
        return {"title_work": title.hex(), "title_work_sha256": sha256_bytes(title),
                "config_work_pointer": config_work_ptr,
                "config_work": config_work.hex(), "config_work_sha256": sha256_bytes(config_work),
                "title_main_global": bytes(uc.mem_read(TITLE_MAIN_GLOBAL, 4)).hex(),
                "title_config_global": bytes(uc.mem_read(TITLE_CONFIG_GLOBAL, 4)).hex(),
                "config": bytes(uc.mem_read(CONFIG, 8)).hex(),
                "return": uc.reg_read(arm.UC_ARM_REG_R0),
                "pc": uc.reg_read(arm.UC_ARM_REG_PC),
                "sp": uc.reg_read(arm.UC_ARM_REG_SP),
                "preserved": saved,
                "trace": json.loads(json.dumps(self.trace)),
                "hook_error": self.hook_error}

    def tick(self, expected_state: int) -> dict:
        uc = self.uc
        title_state = struct.unpack("<I", uc.mem_read(TITLE_MAIN_WORK + 0x9C, 4))[0]
        if title_state != expected_state:
            raise ValueError(f"tick expected State {expected_state}, found {title_state}")
        self._seed_registers()
        try:
            uc.emu_start(CALLBACK, 0, count=100000)
        except unicorn.UcError as exc:
            self.fault = str(exc)
        result = self._snapshot()
        result.update({"fault": self.fault, "stopped": self.stopped,
                       "state": struct.unpack("<I", bytes.fromhex(result["title_work"])[0x9C:0xA0])[0]})
        if self.fault or not self.stopped:
            return result
        self.stopped = False
        return result

    def run(self) -> dict:
        self._seed_registers()
        phases = []
        try:
            uc = self.uc
            uc.emu_start(CALLBACK, 0, count=100000)
            phases.append({"phase": "state9", **self._snapshot(), "fault": None,
                           "stopped": self.stopped,
                           "state": struct.unpack("<I", uc.mem_read(TITLE_MAIN_WORK + 0x9C, 4))[0]})
            if self.scenario["kind"] == "transition":
                self.stopped = False
                phases.append({"phase": "state10-pending", **self.tick(10)})
                phases[-1]["phase"] = "state10-pending"
                self.stopped = False
                phases.append({"phase": "state10-ready-reset", **self.tick(10)})
                phases[-1]["phase"] = "state10-ready-reset"
        except unicorn.UcError as exc:
            self.fault = str(exc)
            phases.append({"phase": "fault", "fault": self.fault, "stopped": False})
        except ValueError as exc:
            # A controlled wrong-path mutant may prevent the expected State-10
            # phase. Record it as a differential failure so the negative
            # control is reported instead of aborting the whole experiment.
            self.fault = f"caller assertion: {exc}"
            phases.append({"phase": "assertion-fault", "fault": self.fault,
                           "stopped": False})
        return {"phases": phases, "task_records": self.task_records,
                "trace": self.trace, "hook_error": self.hook_error,
                "active_calls": self.active_index, "fault": self.fault}


def _phase_projection(run: dict) -> list[dict]:
    projected = []
    for phase in run["phases"]:
        item = {key: phase.get(key) for key in (
        "phase", "title_work", "config_work_pointer", "config_work",
        "title_main_global", "title_config_global", "config", "return", "pc",
        "sp", "preserved", "hook_error", "fault", "stopped", "state")}
        # The candidate executes from an injected address, so return addresses
        # inside its body differ from the pinned original's. Compare the ordered
        # boundary effects and arguments; retain call_site in the report as a
        # diagnostic without treating compiler layout as behavior.
        item["trace"] = [{
            "address": record["address"], "name": record["name"],
            # r0 is the stable primary argument at every observed boundary.
            # Other caller-saved registers are captured in raw evidence and
            # checked explicitly for factory/readiness contracts below.
            "r0": record.get("r0_string", record["r0_r3"][0]),
            "r0_string": record.get("r0_string"),
            "hle_return": record.get("hle_return"),
            "task_handle": record.get("task_handle"),
            "active_result": record.get("active_result")}
            for record in phase["trace"]]
        projected.append(item)
    return projected


def compare_runs(original: dict, candidate: dict) -> str | None:
    for label, run in (("original", original), ("candidate", candidate)):
        if run["fault"]:
            return f"{label} fault: {run['fault']}"
        if run["hook_error"]:
            return f"{label} HLE error: {run['hook_error']}"
        for phase in run["phases"]:
            if not phase.get("stopped"):
                return f"{label} failed to reach callback sentinel at {phase.get('phase')}"
    original_projection = _phase_projection(original)
    candidate_projection = _phase_projection(candidate)
    if original_projection != candidate_projection:
        for index, (left, right) in enumerate(zip(original_projection, candidate_projection)):
            if left != right:
                keys = [key for key in left if left[key] != right.get(key)]
                return f"phase {index} differs in {','.join(keys)}"
        return "phase count differs"
    def task_tuple(record: dict) -> tuple:
        words = record["stack_words"]
        relevant = words[1:4] if record.get("r0_string") == "TITLE_CONFIG_MAIN" else words[1:5]
        return record.get("r0_string"), tuple(relevant), record.get("hle_return")
    if [task_tuple(record) for record in original["task_records"]] != [
            task_tuple(record) for record in candidate["task_records"]]:
        return "process-factory callback/work/task tuple differs"
    return None


def validate_registration(run: dict, expected_config: bytes) -> str | None:
    phases = run["phases"]
    if len(phases) != 3 or [p["phase"] for p in phases] != [
            "state9", "state10-pending", "state10-ready-reset"]:
        return "unexpected transition phase count/order"
    s9, pending, reset = phases
    if s9["state"] != 10 or pending["state"] != 10 or reset["state"] != 5:
        return "State 9/10/reset state sequence is incorrect"
    if s9["config"] != expected_config.hex() or pending["config"] != expected_config.hex() \
            or reset["config"] != expected_config.hex():
        return "config bytes changed during caller-composition run"
    if s9["config_work_pointer"] != TITLE_CONFIG_WORK:
        return "initializer did not publish the expected private TitleConfigWork pointer"
    if struct.unpack("<I", bytes.fromhex(s9["config_work"])[0:4])[0] != CALC_TASK_TOKEN:
        return "Calc task token was not stored at TitleConfigWork+0"
    factories = [record for record in run["task_records"] if record["address"] == "0x00118488"]
    if len(factories) != 2:
        return f"expected Calc and Draw process factory calls, got {len(factories)}"
    calc, draw = factories
    calc_words = [int(value, 16) for value in calc["stack_words"]]
    draw_words = [int(value, 16) for value in draw["stack_words"]]
    if calc.get("r0_string") != "TITLE_CONFIG_MAIN" or calc_words[1:4] != [
            CALC_CALLBACK, SECONDARY_CALLBACK, TITLE_CONFIG_WORK]:
        return "Calc factory tuple does not contain expected callbacks/work context"
    if draw.get("r0_string") != "TITLE_CONFIG D" or draw_words[1:5] != [
            DRAW_CALLBACK, 0, 0, CALC_TASK_TOKEN]:
        return "Draw factory tuple does not contain expected callback/Calc task"
    helper_calls = [record for record in run["trace"] if record["address"] == f"0x{TASK_ACTIVE:08x}"]
    if len(helper_calls) != 2 or [call.get("active_result") for call in helper_calls] != [1, 0] \
            or [call.get("task_handle") for call in helper_calls] != [
                f"0x{CALC_TASK_TOKEN:08x}", f"0x{CALC_TASK_TOKEN:08x}"]:
        return "readiness did not query the registered Calc token as active then inactive"
    reset_calls = [record["address"] for record in run["trace"]
                   if record["address"] in {"0x002b8b78", "0x002b88c4", "0x00275e58",
                                             "0x002a0c54", "0x002a06dc"}]
    expected_reset = ["0x002b8b78", "0x002b8b78", "0x002b88c4", "0x002b88c4",
                      "0x002b88c4", "0x002b88c4", "0x00275e58", "0x002a0c54",
                      "0x002a06dc"]
    if reset_calls != expected_reset:
        return f"reset helper order mismatch: {reset_calls}"
    reset_arg_error = validate_reset_arguments(run["trace"])
    if reset_arg_error:
        return reset_arg_error
    title = bytes.fromhex(reset["title_work"])
    if struct.unpack_from("<ff", title, 0x64) != (0.0, 0.0):
        return "Title_ResetForBoot did not zero fade fields"
    if struct.unpack_from("<HHHH", title, 0x74) != (0x210, 0x211, 0x212, 0x213):
        return "reset did not store all four deterministic touch handles"
    if (title[0x61], title[0x84], title[0x85], title[0x96]) != (0, 1, 1, 1):
        return "reset flag stores differ from the State-10 reset path"
    if any(phase["fault"] for phase in phases) or any(phase["hook_error"] for phase in phases):
        return "phase fault/HLE error"
    return None


def validate_gate(run: dict) -> str | None:
    if len(run["phases"]) != 1:
        return "State-9 flag gate unexpectedly continued into State 10"
    phase = run["phases"][0]
    if phase["state"] != 9:
        return "State-9 flag gate changed the title state"
    if run["task_records"] or phase["config_work_pointer"] != 0xDEAD0001:
        return "State-9 flag gate reached initializer/task creation"
    if any(item["address"] in (f"0x{INIT:08x}", "0x002A7604", "0x002C4B84", "0x00118488")
           for item in run["trace"]):
        return "State-9 flag gate did not suppress transition/init/task calls"
    return None


def validate_reset_arguments(trace: list[dict]) -> str | None:
    """Check the consumed arguments at each Title_ResetForBoot HLE boundary.

    Call-site-specific expectations follow the pinned MainTitle callback. The
    Sound_PlaySE prototype is one argument, so its observed r1 is diagnostic
    only; the other checks below cover only the registers consumed by their
    respective declared helper call shapes.
    """
    expected = {
        "0x001ea3f0": ("0x002b8b78", ("0x0000009f",)),
        "0x001ea3fc": ("0x002b88c4", ("0x00000011", "0x00000014")),
        "0x001ea40c": ("0x002b88c4", ("0x00000011", "0x00000015")),
        "0x001ea41c": ("0x002b88c4", ("0x00000011", "0x00000018")),
        "0x001ea42c": ("0x002b88c4", ("0x00000011", "0x00000019")),
        "0x001ea440": ("0x00275e58", ("0x00000002",)),
        "0x001ea454": ("0x002a0c54", ("title/title_top.bcenv", "0x00000000")),
        "0x001ea464": ("0x002a06dc", ("0xcafe0088", "0x00000000")),
    }
    sound_records = [record for record in trace if record.get("address") == "0x002b8b78"]
    if [record["r0_r3"][0] for record in sound_records] != [
            "0x00000099", "0x0000009f"]:
        return "Sound_PlaySE consumed se_id sequence differs from init 0x99 then reset 0x9f"
    actual = {record["call_site"]: record for record in trace
              if record.get("call_site") in expected}
    if set(actual) != set(expected):
        return f"reset HLE call-site set mismatch: {sorted(actual)}"
    for site, (address, args) in expected.items():
        record = actual[site]
        if record["address"] != address:
            return f"reset call {site} reached {record['address']}, expected {address}"
        regs = record["r0_r3"]
        # String arguments are decoded, while other helpers use the leading
        # integer argument registers shown in the pinned caller.
        if address == "0x002a0c54":
            got = (record.get("r0_string"), regs[1])
        elif address == "0x002a06dc":
            got = tuple(regs[:2])
        elif address == "0x002b88c4":
            got = tuple(regs[:2])
        else:
            got = tuple(regs[:1])
        if got != args:
            return f"reset consumed arguments mismatch at {site}: {got!r} != {args!r}"
    return None


def experiment(code_path: Path, output: Path, calc_image_path: Path | None = None,
               allow_combined_image: bool = False,
               final_initializer: bool = False,
               integrated_manifest_path: Path | None = None) -> dict:
    output.mkdir(parents=True, exist_ok=False)
    started = time.perf_counter()
    game = json.loads((ROOT / "config/game_info.json").read_text(encoding="utf-8"))
    image = code_path.read_bytes()
    if len(image) != game["code_bin_size"] or sha256_bytes(image) != EXPECTED_CODE_SHA256 \
            or sha256_bytes(image) != game["code_sha256"]:
        raise ValueError("--code must be the pinned configured code image")
    if len(image) > TEXT_MAP_SIZE:
        raise ValueError("pinned code image exceeds caller-machine text map")
    calc_image = image
    calc_image_hash = None
    if calc_image_path is not None:
        calc_image = calc_image_path.read_bytes()
        calc_image_hash = sha256_bytes(calc_image)
        if len(calc_image) != len(image):
            raise ValueError("patched image must have the same size as pinned code.bin")
        if not allow_combined_image and calc_image_hash != EXPECTED_CALC_PATCH_SHA256:
            raise ValueError("--calc-image must be the reviewed production-derived Calc patch")
    if final_initializer:
        if not allow_combined_image or integrated_manifest_path is None:
            raise ValueError("--final-initializer requires --patched-image and its --manifest")
        manifest = json.loads(integrated_manifest_path.read_text(encoding="utf-8"))
        if manifest.get("patched_sha256") != calc_image_hash:
            raise ValueError("integrated manifest does not identify the supplied patched image")
        placements = manifest.get("placements", {})
        if "initializer" not in placements or "ready_gate" not in placements:
            raise ValueError("final initializer mode requires production initializer and ready-gate placements")
    candidate, build = compile_candidate(output)
    wrong_callback, control_meta = make_candidate_negative_control(candidate)

    cases = []
    first_counterexample = None
    for spec in scenario_specs():
        original = CallerMachine(image, None, spec).run()
        patched = CallerMachine(calc_image, None if final_initializer else candidate,
                                spec).run()
        difference = compare_runs(original, patched)
        expected = validate_registration(patched, spec["config"]) if spec["kind"] == "transition" else validate_gate(patched)
        original_expected = validate_registration(original, spec["config"]) if spec["kind"] == "transition" else validate_gate(original)
        passed = difference is None and expected is None and original_expected is None
        row = {"case": spec["label"], "passed": passed,
               "difference": difference, "original_expectation": original_expected,
               "patched_expectation": expected,
               "original_phase_states": [p.get("state") for p in original["phases"]],
               "patched_phase_states": [p.get("state") for p in patched["phases"]],
               "original_trace": original["trace"], "patched_trace": patched["trace"],
               "original_task_records": original["task_records"],
               "patched_task_records": patched["task_records"]}
        cases.append(row)
        if not passed and first_counterexample is None:
            first_counterexample = {"case": spec["label"], "difference": difference,
                                    "original_expectation": original_expected,
                                    "patched_expectation": expected}

    negative_spec = dict(scenario_specs()[0])
    original_negative = CallerMachine(image, None, negative_spec).run()
    mutant_negative = CallerMachine(calc_image, wrong_callback, negative_spec).run()
    mutant_reason = validate_registration(mutant_negative, negative_spec["config"])
    negative_detected = mutant_reason is not None and compare_runs(original_negative, mutant_negative) is not None
    negative = {**control_meta, "detected": negative_detected,
                "mutant_expectation_failure": mutant_reason,
                "trace_differs": compare_runs(original_negative, mutant_negative)}

    passed = all(row["passed"] for row in cases) and negative_detected
    report = {
        "schema": 1, "passed": passed,
        "scope": "pinned MainTitle State 9/10 caller + TitleConfig initializer differential under matched explicit HLE boundaries",
        "reference_sha256": sha256_bytes(image),
        "production_calc_image_sha256": calc_image_hash,
        "integrated_image_mode": "combined" if allow_combined_image else ("calc-only" if calc_image_path else "original"),
        "source_sha256": sha256_file(INIT_SOURCE),
        "runner_sha256": sha256_file(Path(__file__)),
        "object_sha256": build["object_sha256"],
        "build": build,
        "layout": {"text": [hex(TEXT), hex(TEXT_MAP_SIZE)],
                   "title_main_work": hex(TITLE_MAIN_WORK),
                   "title_config_work": hex(TITLE_CONFIG_WORK),
                   "stack_pointer": hex(INITIAL_SP),
                   "initializer_patch": {"from": hex(INIT),
                                         "to": hex(INIT if final_initializer else INIT_INJECT),
                                         "mode": "production-in-place" if final_initializer else "experiment-injection"}},
        "production_initializer_mode": final_initializer,
        "integrated_manifest_sha256": (sha256_file(integrated_manifest_path)
                                       if integrated_manifest_path else None),
        "case_count": len(cases), "cases_passed": sum(row["passed"] for row in cases),
        "first_counterexample": first_counterexample,
        "negative_control": negative,
        "argument_contract_checks": {
            "sound_play_se": {
                "prototype": "void Sound_PlaySE(s32 se_id)",
                "callee": "0x002B8B78",
                "consumed_argument": "r0 only",
                "expected_r0_sequence": ["0x00000099", "0x0000009f"],
                "r1_r3": "retained as raw diagnostics; not consumed by the one-argument callee"
            },
            "reset_hles": "call-site-specific consumed register/string arguments asserted by validate_reset_arguments"
        },
        "evidence": {"compiled": "passed", "arm_differential": "passed" if passed else "failed",
                     "caller": "partial", "runtime": "not_run"},
        "limits": [
            "The pinned original MainTitle caller and TitleConfig_IsReady body execute, but allocator, process factory, task-active lookup, sprite/resource/cursor setup, Sound_PlaySE internals, transition, touch registration, cursor mode, environment load, and model visibility are explicit matched HLEs. Consumed arguments at the observed reset HLE call sites are asserted; this does not validate those helpers' internal effects.",
            "Callback registration and TitleConfigWork handle linkage are compared; neither registered Calc, Draw, nor Secondary callback is scheduled or executed.",
            "Only State 9, State-10 pending, ready/reset, and the flag_7c gate are covered. State-1 input/cursor behavior, rendering, editing, persistence, profile behavior, Azahar/RSP, and whole-game equivalence are not established.",
            "The two config blocks cover initializer mapping/copy composition only; mapper candidate behavior is not validated by this runner."
        ],
        "cases": cases,
        "elapsed_seconds": round(time.perf_counter() - started, 3)
    }
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code", type=Path, default=CODE_DEFAULT)
    parser.add_argument("--output", type=Path, required=True,
                        help="new task-local output directory")
    parser.add_argument("--calc-image", type=Path,
                        help="reviewed production-derived Calc-patched code image")
    parser.add_argument("--patched-image", type=Path,
                        help="integrated production-derived image (for combined patch composition)")
    parser.add_argument("--manifest", type=Path,
                        help="combined patch manifest, required for --final-initializer")
    parser.add_argument("--final-initializer", action="store_true",
                        help="execute the production initializer from the patched image instead of injecting the experiment candidate")
    args = parser.parse_args(argv)
    if args.calc_image and args.patched_image:
        parser.error("choose only one of --calc-image and --patched-image")
    if args.final_initializer and not args.patched_image:
        parser.error("--final-initializer requires --patched-image")
    if args.final_initializer and not args.manifest:
        parser.error("--final-initializer requires --manifest")
    image_path = args.patched_image or args.calc_image
    report = experiment(args.code, args.output, image_path,
                        allow_combined_image=bool(args.patched_image),
                        final_initializer=args.final_initializer,
                        integrated_manifest_path=args.manifest)
    print(json.dumps({"passed": report["passed"], "report": str(args.output / "report.json"),
                      "cases": report["cases_passed"], "negative_control": report["negative_control"]},
                     indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
